from flask import Blueprint, render_template, redirect, url_for, flash, request, session
import pymysql
from datetime import datetime
from config import Config

tickets_bp = Blueprint('tickets', __name__)


def get_db_connection():
    """Get MySQL database connection"""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )


def require_login():
    """Check if user is logged in"""
    return 'user_id' in session


def require_role(roles):
    """Check if user has required role"""
    if 'user_id' not in session:
        return False
    if isinstance(roles, str):
        roles = [roles]
    return session.get('role') in roles


@tickets_bp.route('/')
def index():
    """Redirect to dashboard or login"""
    if not require_login():
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.dashboard'))


@tickets_bp.route('/all')
def all_tickets():
    """View all tickets (for directors and final authorizers)"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['director', 'final_authorizer', 'admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    status_filter = request.args.get('status', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, u.full_name as user_name, d.name as division_name
            FROM tickets t
            JOIN users u ON t.user_id = u.id
            JOIN divisions d ON t.division_id = d.id
        """
        
        if status_filter:
            query += f" WHERE t.status = '{status_filter}'"
        
        query += " ORDER BY t.created_at DESC"
        
        cursor.execute(query)
        tickets = cursor.fetchall()
        conn.close()
        
        # Convert Decimal to float for JSON serialization
        for ticket in tickets:
            if ticket.get('estimated_cost'):
                ticket['estimated_cost'] = float(ticket['estimated_cost'])
                
    except Exception as e:
        flash(f'Error loading tickets: {str(e)}', 'danger')
        tickets = []
    
    return render_template('tickets/all_tickets.html', tickets=tickets, status_filter=status_filter)


@tickets_bp.route('/my')
def my_tickets():
    """View user's own tickets"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, d.name as division_name
            FROM tickets t
            JOIN divisions d ON t.division_id = d.id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        """, (session['user_id'],))
        tickets = cursor.fetchall()
        conn.close()
        
        # Convert Decimal to float
        for ticket in tickets:
            if ticket.get('estimated_cost'):
                ticket['estimated_cost'] = float(ticket['estimated_cost'])
                
    except Exception as e:
        flash(f'Error loading tickets: {str(e)}', 'danger')
        tickets = []
    
    return render_template('tickets/my_tickets.html', tickets=tickets)


@tickets_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new travel request"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    if session.get('role') != 'employee':
        flash('Only employees can create travel requests', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        destination = request.form.get('destination', '').strip()
        purpose = request.form.get('purpose', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        estimated_cost = request.form.get('estimated_cost')
        
        # Validation
        errors = []
        if not destination:
            errors.append('Destination is required')
        if not purpose:
            errors.append('Purpose is required')
        if not start_date or not end_date:
            errors.append('Start and end dates are required')
        if start_date and end_date and start_date > end_date:
            errors.append('End date must be after start date')
        if not estimated_cost or float(estimated_cost) <= 0:
            errors.append('Valid estimated cost is required')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('tickets.create'))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tickets (user_id, division_id, destination, purpose, start_date, end_date, estimated_cost, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (session['user_id'], session['division_id'], destination, purpose, start_date, end_date, estimated_cost))
            
            conn.commit()
            conn.close()
            
            flash('Travel request submitted successfully!', 'success')
            return redirect(url_for('tickets.my_tickets'))
            
        except Exception as e:
            flash(f'Error creating ticket: {str(e)}', 'danger')
    
    # Get user's division
    division_name = ''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM divisions WHERE id = %s", (session.get('division_id'),))
        result = cursor.fetchone()
        if result:
            division_name = result['name']
        conn.close()
    except:
        pass
    
    return render_template('tickets/create.html', division_name=division_name)


@tickets_bp.route('/<int:ticket_id>')
def view(ticket_id):
    """View ticket details"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        cursor.execute("""
            SELECT t.*, u.full_name as user_name, d.name as division_name
            FROM tickets t
            JOIN users u ON t.user_id = u.id
            JOIN divisions d ON t.division_id = d.id
            WHERE t.id = %s
        """, (ticket_id,))
        ticket = cursor.fetchone()
        
        if not ticket:
            flash('Ticket not found', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Check access
        if session.get('role') == 'employee' and ticket['user_id'] != session['user_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Get approval history
        cursor.execute("""
            SELECT a.*, u.full_name as approver_name
            FROM approvals a
            JOIN users u ON a.approver_id = u.id
            WHERE a.ticket_id = %s
            ORDER BY a.created_at ASC
        """, (ticket_id,))
        approvals = cursor.fetchall()
        
        conn.close()
        
        # Convert Decimal
        if ticket.get('estimated_cost'):
            ticket['estimated_cost'] = float(ticket['estimated_cost'])
            
    except Exception as e:
        flash(f'Error loading ticket: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('tickets/view.html', ticket=ticket, approvals=approvals)


@tickets_bp.route('/<int:ticket_id>/approve', methods=['POST'])
def approve(ticket_id):
    """Approve ticket at director or final level"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['director', 'final_authorizer', 'admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    comments = request.form.get('comments', '').strip()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        
        if not ticket:
            flash('Ticket not found', 'danger')
            return redirect(url_for('tickets.all_tickets'))
        
        # Determine approval level and new status
        if session.get('role') == 'final_authorizer' and ticket['status'] == 'director_approved':
            # Final approval
            new_status = 'approved'
            level = 'final'
        elif session.get('role') in ['director', 'admin'] and ticket['status'] == 'pending':
            # Director approval
            new_status = 'director_approved'
            level = 'director'
        else:
            flash('Ticket cannot be approved at this stage', 'warning')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        # Update ticket status
        cursor.execute("UPDATE tickets SET status = %s WHERE id = %s", (new_status, ticket_id))
        
        # Record approval
        cursor.execute("""
            INSERT INTO approvals (ticket_id, approver_id, level, action, comments)
            VALUES (%s, %s, %s, 'approved', %s)
        """, (ticket_id, session['user_id'], level, comments))
        
        conn.commit()
        conn.close()
        
        flash(f'Ticket #{ticket_id} approved successfully!', 'success')
        
    except Exception as e:
        flash(f'Error approving ticket: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))


@tickets_bp.route('/<int:ticket_id>/reject', methods=['POST'])
def reject(ticket_id):
    """Reject ticket"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['director', 'final_authorizer', 'admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    comments = request.form.get('comments', '').strip()
    
    if not comments:
        flash('Rejection reason is required', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        
        if not ticket:
            flash('Ticket not found', 'danger')
            return redirect(url_for('tickets.all_tickets'))
        
        if ticket['status'] in ['approved', 'rejected']:
            flash('Ticket already processed', 'warning')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        # Determine level
        if session.get('role') == 'final_authorizer':
            level = 'final'
        else:
            level = 'director'
        
        # Update ticket status
        cursor.execute("UPDATE tickets SET status = 'rejected' WHERE id = %s", (ticket_id,))
        
        # Record rejection
        cursor.execute("""
            INSERT INTO approvals (ticket_id, approver_id, level, action, comments)
            VALUES (%s, %s, %s, 'rejected', %s)
        """, (ticket_id, session['user_id'], level, comments))
        
        conn.commit()
        conn.close()
        
        flash(f'Ticket #{ticket_id} has been rejected', 'warning')
        
    except Exception as e:
        flash(f'Error rejecting ticket: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))
