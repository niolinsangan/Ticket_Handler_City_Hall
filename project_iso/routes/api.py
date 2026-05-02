from flask import Blueprint, jsonify, request, session, Response
from db import execute_query, get_db_type
import datetime
import queue
from broadcast import clients, clients_lock, broadcast_event

api_bp = Blueprint('api', __name__, url_prefix='/api')

def require_login():
    """Check session login for API (session-based auth)"""
    return 'user_id' in session

def require_role(roles):
    """Require role for API"""
    if not require_login():
        return False
    if isinstance(roles, str):
        roles = [roles]
    return session.get('role') in roles

@api_bp.route('/tickets', methods=['GET', 'POST'])
def tickets_api():
    if not require_login():
        return jsonify({'error': 'Unauthorized'}), 401

    db_type = get_db_type()

    if request.method == 'GET':
        # List tickets based on role
        if require_role('employee'):
            params = (session['user_id'],)
            query = """
                SELECT t.*, d.name as division_name 
                FROM tickets t JOIN divisions d ON t.division_id = d.id 
                WHERE t.user_id = ?
            """ if db_type == 'sqlite' else """
                SELECT t.*, d.name as division_name 
                FROM tickets t JOIN divisions d ON t.division_id = d.id 
                WHERE t.user_id = %s
            """
        else:
            query = """
                SELECT t.*, u.full_name as user_name, d.name as division_name
                FROM tickets t 
                JOIN users u ON t.user_id = u.id 
                JOIN divisions d ON t.division_id = d.id
            """
            params = ()

        tickets = execute_query(query, params=params, fetch_all=True)
        return jsonify({'tickets': tickets or []})

    elif request.method == 'POST':
        if not require_role('employee'):
            return jsonify({'error': 'Forbidden'}), 403

        data = request.get_json()
        if not data or not all(k in data for k in ['destination', 'purpose', 'start_date', 'end_date', 'division_id']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validation
        if data['start_date'] >= data['end_date']:
            return jsonify({'error': 'Invalid dates'}), 400

        params = (
            session['user_id'], data['division_id'], data['destination'], data['purpose'],
            data.get('associates'), data['start_date'], data['end_date'],
            data.get('vehicle_needed', 'no'), 'pending'
        )
        query = """
            INSERT INTO tickets (user_id, division_id, destination, purpose, associates, 
                                start_date, end_date, vehicle_needed, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if db_type == 'sqlite' else """
            INSERT INTO tickets (user_id, division_id, destination, purpose, associates, 
                                start_date, end_date, vehicle_needed, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        ticket_id = execute_query(query, params=params, commit=True)
        return jsonify({'id': ticket_id, 'message': 'Ticket created'}), 201

@api_bp.route('/tickets/<int:ticket_id>', methods=['GET', 'PUT', 'DELETE'])
def ticket_api(ticket_id):
    if not require_login():
        return jsonify({'error': 'Unauthorized'}), 401

    db_type = get_db_type()

    if request.method == 'GET':
        params = (ticket_id,)
        query = "SELECT * FROM tickets WHERE id = ?" if db_type == 'sqlite' else "SELECT * FROM tickets WHERE id = %s"
        ticket = execute_query(query, params=params, fetch_one=True)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        # Check access (owner or admin)
        if not require_role(['admin']) and ticket['user_id'] != session['user_id']:
            return jsonify({'error': 'Forbidden'}), 403
        return jsonify(ticket)

    elif request.method == 'PUT':
        ticket = execute_query("SELECT * FROM tickets WHERE id = ? OR id = %s", params=(ticket_id,), fetch_one=True)
        if not ticket or ticket['user_id'] != session['user_id'] or ticket['status'] != 'pending':
            return jsonify({'error': 'Forbidden or invalid state'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON required'}), 400

        params = (
            data.get('destination', ticket['destination']),
            data.get('purpose', ticket['purpose']),
            data.get('associates', ticket['associates']),
            data.get('start_date', ticket['start_date']),
            data.get('end_date', ticket['end_date']),
            data.get('vehicle_needed', ticket['vehicle_needed']),
            ticket_id
        )
        query = """
            UPDATE tickets SET destination=?, purpose=?, associates=?, start_date=?, end_date=?, vehicle_needed=?
            WHERE id=?
        """ if db_type == 'sqlite' else """
            UPDATE tickets SET destination=%s, purpose=%s, associates=%s, start_date=%s, end_date=%s, vehicle_needed=%s
            WHERE id=%s
        """
        execute_query(query, params=params, commit=True)
        return jsonify({'message': 'Updated'})

    elif request.method == 'DELETE':
        if not require_role(['admin', 'employee']):
            return jsonify({'error': 'Forbidden'}), 403
        ticket = execute_query("SELECT * FROM tickets WHERE id = ? OR id = %s", params=(ticket_id,), fetch_one=True)
        if not ticket or (ticket['user_id'] != session['user_id'] and not require_role('admin')):
            return jsonify({'error': 'Forbidden'}), 403
        execute_query("DELETE FROM tickets WHERE id = ? OR id = %s", params=(ticket_id,), commit=True)
        return jsonify({'message': 'Deleted'})

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing credentials'}), 400

    from routes.auth import get_db_connection, dict_from_row
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt()

    db_type = get_db_type()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
            row = cursor.fetchone()
            user = dict_from_row(row) if row else None
        else:
            cursor.execute("SELECT * FROM users WHERE username = %s", (data['username'],))
            user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], data['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['division_id'] = user.get('division_id')
            return jsonify({'message': 'Logged in', 'user': {'id': user['id'], 'role': user['role'], 'name': user['full_name']}})
        return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        conn.close()

@api_bp.errorhandler(404)
def api_not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_bp.route('/stream')
def stream():
    """Server-Sent Events endpoint for real-time dashboard refresh."""
    def event_stream():
        q = queue.Queue(maxsize=10)
        with clients_lock:
            clients.append(q)
        try:
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield f"data: {msg}\n\n"
                except queue.Empty:
                    yield ":heartbeat\n\n"
        finally:
            with clients_lock:
                if q in clients:
                    clients.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


@api_bp.errorhandler(405)
def api_method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405

