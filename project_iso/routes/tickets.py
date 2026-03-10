from flask import Blueprint, render_template, redirect, url_for, flash, request, session
import sqlite3
import pymysql
from datetime import datetime
from config import Config

tickets_bp = Blueprint('tickets', __name__)


def get_db_connection():
    """Get database connection based on configuration"""
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    if db_type == 'sqlite':
        conn = sqlite3.connect(Config.SQLITE_DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        return pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )


def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(zip(row.keys(), row))


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
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
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
            # Validate status_filter to prevent SQL injection
            allowed_statuses = ['pending', 'director_approved', 'approved', 'rejected']
            if status_filter in allowed_statuses:
                if db_type == 'sqlite':
                    query += " WHERE t.status = ?"
                    params = (status_filter,)
                else:
                    query += " WHERE t.status = %s"
                    params = (status_filter,)
            else:
                params = ()
        
        query += " ORDER BY t.created_at DESC"
        
        if status_filter and status_filter in allowed_statuses:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            tickets = [dict_from_row(row) for row in rows]
        else:
            tickets = cursor.fetchall()
        
        conn.close()
        
        # Convert date strings to datetime objects for strftime in templates
        for ticket in tickets:
            if ticket.get('start_date') and isinstance(ticket.get('start_date'), str):
                ticket['start_date'] = datetime.strptime(ticket['start_date'], '%Y-%m-%d').date()
            if ticket.get('end_date') and isinstance(ticket.get('end_date'), str):
                ticket['end_date'] = datetime.strptime(ticket['end_date'], '%Y-%m-%d').date()
                
            
    except Exception as e:
        flash(f'Error loading tickets: {str(e)}', 'danger')
        tickets = []
    
    return render_template('tickets/all_tickets.html', tickets=tickets, status_filter=status_filter)


@tickets_bp.route('/my')
def my_tickets():
    """View user's own tickets"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("""
                SELECT t.*, d.name as division_name
                FROM tickets t
                JOIN divisions d ON t.division_id = d.id
                WHERE t.user_id = ?
                ORDER BY t.created_at DESC
            """, (session['user_id'],))
        else:
            cursor.execute("""
                SELECT t.*, d.name as division_name
                FROM tickets t
                JOIN divisions d ON t.division_id = d.id
                WHERE t.user_id = %s
                ORDER BY t.created_at DESC
            """, (session['user_id'],))
        
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            tickets = [dict_from_row(row) for row in rows]
        else:
            tickets = cursor.fetchall()
        
        conn.close()
        
        # Convert date strings to datetime objects for strftime in templates
        for ticket in tickets:
            if ticket.get('start_date') and isinstance(ticket.get('start_date'), str):
                ticket['start_date'] = datetime.strptime(ticket['start_date'], '%Y-%m-%d').date()
            if ticket.get('end_date') and isinstance(ticket.get('end_date'), str):
                ticket['end_date'] = datetime.strptime(ticket['end_date'], '%Y-%m-%d').date()
                
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
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    if request.method == 'POST':
        destination = request.form.get('destination', '').strip()
        purpose = request.form.get('purpose', '').strip()
        associates = request.form.get('associates', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
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
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('tickets.create'))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if db_type == 'sqlite':
                cursor.execute("""
                    INSERT INTO tickets (user_id, division_id, destination, purpose, associates, start_date, end_date, vehicle_needed, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'no', 'pending')
                """, (session['user_id'], session['division_id'], destination, purpose, associates, start_date, end_date))
            else:
                cursor.execute("""
                    INSERT INTO tickets (user_id, division_id, destination, purpose, associates, start_date, end_date, vehicle_needed, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'no', 'pending')
                """, (session['user_id'], session['division_id'], destination, purpose, associates, start_date, end_date))
            
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
        
        if db_type == 'sqlite':
            cursor.execute("SELECT name FROM divisions WHERE id = ?", (session.get('division_id'),))
        else:
            cursor.execute("SELECT name FROM divisions WHERE id = %s", (session.get('division_id'),))
        
        result = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
        if result:
            division_name = result['name']
        conn.close()
    except:
        pass
    
    return render_template('tickets/create.html', division_name=division_name)


@tickets_bp.route('/<int:ticket_id>/edit', methods=['GET', 'POST'])
def edit(ticket_id):
    """Edit existing travel request (only for pending tickets)"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        else:
            cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        
        ticket = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
        
        if not ticket:
            flash('Ticket not found', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Check if user owns the ticket
        if ticket['user_id'] != session['user_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Only allow editing pending tickets
        if ticket['status'] != 'pending':
            flash('Only pending tickets can be edited', 'warning')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        # Handle form submission
        if request.method == 'POST':
            destination = request.form.get('destination', '').strip()
            purpose = request.form.get('purpose', '').strip()
            associates = request.form.get('associates', '').strip()
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
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
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('tickets.edit', ticket_id=ticket_id))
            
            # Update ticket
            if db_type == 'sqlite':
                cursor.execute("""
                    UPDATE tickets 
                    SET destination = ?, purpose = ?, associates = ?, start_date = ?, end_date = ?
                    WHERE id = ?
                """, (destination, purpose, associates, start_date, end_date, ticket_id))
            else:
                cursor.execute("""
                    UPDATE tickets 
                    SET destination = %s, purpose = %s, associates = %s, start_date = %s, end_date = %s
                    WHERE id = %s
                """, (destination, purpose, associates, start_date, end_date, ticket_id))
            
            conn.commit()
            conn.close()
            
            flash('Travel request updated successfully!', 'success')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        conn.close()
        
    except Exception as e:
        flash(f'Error loading ticket: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('tickets/edit.html', ticket=ticket)


@tickets_bp.route('/<int:ticket_id>')
def view(ticket_id):
    """View ticket details"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        if db_type == 'sqlite':
            cursor.execute("""
                SELECT t.*, u.full_name as user_name, d.name as division_name
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                JOIN divisions d ON t.division_id = d.id
                WHERE t.id = ?
            """, (ticket_id,))
        else:
            cursor.execute("""
                SELECT t.*, u.full_name as user_name, d.name as division_name
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                JOIN divisions d ON t.division_id = d.id
                WHERE t.id = %s
            """, (ticket_id,))
        
        ticket = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
        
        if not ticket:
            flash('Ticket not found', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Check access
        if session.get('role') == 'employee' and ticket['user_id'] != session['user_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Get approval history
        if db_type == 'sqlite':
            cursor.execute("""
                SELECT a.*, u.full_name as approver_name
                FROM approvals a
                JOIN users u ON a.approver_id = u.id
                WHERE a.ticket_id = ?
                ORDER BY a.created_at ASC
            """, (ticket_id,))
        else:
            cursor.execute("""
                SELECT a.*, u.full_name as approver_name
                FROM approvals a
                JOIN users u ON a.approver_id = u.id
                WHERE a.ticket_id = %s
                ORDER BY a.created_at ASC
            """, (ticket_id,))
        
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            approvals = [dict_from_row(row) for row in rows]
        else:
            approvals = cursor.fetchall()
        
        conn.close()
        
        # Convert date strings to datetime objects for strftime in templates
        if ticket.get('start_date') and isinstance(ticket.get('start_date'), str):
            ticket['start_date'] = datetime.strptime(ticket['start_date'], '%Y-%m-%d').date()
        if ticket.get('end_date') and isinstance(ticket.get('end_date'), str):
            ticket['end_date'] = datetime.strptime(ticket['end_date'], '%Y-%m-%d').date()
        
        # Convert approval timestamps as well
        for approval in approvals:
            if approval.get('created_at') and isinstance(approval.get('created_at'), str):
                approval['created_at'] = datetime.strptime(approval['created_at'], '%Y-%m-%d %H:%M:%S')
            
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
    vehicle_assigned = request.form.get('vehicle_assigned', '').strip()
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        else:
            cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        
        ticket = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
        
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
        
        # Update ticket status and vehicle assignment (for admin)
        if session.get('role') == 'admin' and vehicle_assigned:
            if db_type == 'sqlite':
                cursor.execute("UPDATE tickets SET status = ?, vehicle_assigned = ? WHERE id = ?", (new_status, vehicle_assigned, ticket_id))
            else:
                cursor.execute("UPDATE tickets SET status = %s, vehicle_assigned = %s WHERE id = %s", (new_status, vehicle_assigned, ticket_id))
        else:
            if db_type == 'sqlite':
                cursor.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
            else:
                cursor.execute("UPDATE tickets SET status = %s WHERE id = %s", (new_status, ticket_id))
        
        # Record approval
        if db_type == 'sqlite':
            cursor.execute("""
                INSERT INTO approvals (ticket_id, approver_id, level, action, comments)
                VALUES (?, ?, ?, 'approved', ?)
            """, (ticket_id, session['user_id'], level, comments))
        else:
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
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    if not comments:
        flash('Rejection reason is required', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        else:
            cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        
        ticket = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
        
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
        if db_type == 'sqlite':
            cursor.execute("UPDATE tickets SET status = 'rejected' WHERE id = ?", (ticket_id,))
        else:
            cursor.execute("UPDATE tickets SET status = 'rejected' WHERE id = %s", (ticket_id,))
        
        # Record rejection
        if db_type == 'sqlite':
            cursor.execute("""
                INSERT INTO approvals (ticket_id, approver_id, level, action, comments)
                VALUES (?, ?, ?, 'rejected', ?)
            """, (ticket_id, session['user_id'], level, comments))
        else:
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
