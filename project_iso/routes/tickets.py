from flask import Blueprint, render_template, redirect, url_for, flash, request, session
import sqlite3
import pymysql
from datetime import datetime
from config import Config

tickets_bp = Blueprint('tickets', __name__)
from db import get_db_connection, dict_from_row, get_db_type


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


def get_available_vehicles():
    """Get list of available vehicles for assignment"""
    db_type = get_db_type()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("SELECT id, name FROM vehicles WHERE status = 'available' ORDER BY name")
        else:
            cursor.execute("SELECT id, name FROM vehicles WHERE status = 'available' ORDER BY name")
        
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            vehicles = [dict_from_row(row) for row in rows]
        else:
            vehicles = cursor.fetchall()
        
        conn.close()
        return vehicles
    except Exception as e:
        print(f"Error getting vehicles: {e}")
        return []


@tickets_bp.route('/vehicles', methods=['GET', 'POST'])
def vehicles():
    """Admin vehicle management"""
    if not require_login() or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db_type = get_db_type()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            vehicle_type = request.form.get('vehicle_type', 'car')
            status = request.form.get('status', 'available')
            if name:
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if db_type == 'sqlite':
                        cursor.execute("INSERT INTO vehicles (name, vehicle_type, status) VALUES (?, ?, ?)", (name, vehicle_type, status))
                    else:
                        cursor.execute("INSERT INTO vehicles (name, vehicle_type, status) VALUES (%s, %s, %s)", (name, vehicle_type, status))
                    conn.commit()
                    flash(f'Vehicle {name} added.', 'success')
                except Exception as e:
                    if conn:
                        conn.rollback()
                    flash(f'Error adding vehicle: {e}', 'danger')
                finally:
                    if conn:
                        conn.close()
            else:
                flash('Name is required', 'danger')
        elif action == 'delete':
            vehicle_id = request.form.get('vehicle_id')
            if vehicle_id:
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if db_type == 'sqlite':
                        cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
                    else:
                        cursor.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))
                    conn.commit()
                    flash('Vehicle deleted.', 'success')
                except Exception as e:
                    if conn:
                        conn.rollback()
                    flash(f'Error deleting vehicle: {e}', 'danger')
                finally:
                    if conn:
                        conn.close()
        elif action == 'update_status':
            vehicle_id = request.form.get('vehicle_id')
            new_status = request.form.get('new_status')
            if vehicle_id and new_status in ['available', 'assigned', 'maintenance']:
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if db_type == 'sqlite':
                        cursor.execute("UPDATE vehicles SET status = ? WHERE id = ?", (new_status, vehicle_id))
                    else:
                        cursor.execute("UPDATE vehicles SET status = %s WHERE id = %s", (new_status, vehicle_id))
                    conn.commit()
                    flash(f'Vehicle status updated to {new_status}.', 'success')
                except Exception as e:
                    if conn:
                        conn.rollback()
                    flash(f'Error updating status: {e}', 'danger')
                finally:
                    if conn:
                        conn.close()
    
    # Get all vehicles
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM vehicles ORDER BY name")
        else:
            cursor.execute("SELECT * FROM vehicles ORDER BY name")
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            vehicles = [dict_from_row(row) for row in rows]
        else:
            vehicles = cursor.fetchall()
    except Exception as e:
        flash(f'Error loading vehicles: {e}', 'danger')
        vehicles = []
    finally:
        if conn:
            conn.close()
    
    return render_template('tickets/vehicles.html', vehicles=vehicles)


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
    db_type = get_db_type()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, u.full_name as user_name, d.name as division_name,
                   v.name as vehicle_name
            FROM tickets t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN divisions d ON t.division_id = d.id
            LEFT JOIN vehicles v ON t.vehicle_assigned = v.name
        """
        
        if status_filter:
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
        else:
            params = ()
        
        query += " ORDER BY t.created_at DESC"
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if db_type == 'sqlite':
            rows = cursor.fetchall()
            tickets = [dict_from_row(row) for row in rows]
        else:
            tickets = cursor.fetchall()
        
        conn.close()
        
        # Convert dates
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
    
    division_id = session.get('division_id')
    if not division_id:
        flash('You do not have a division assigned and cannot create tickets.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    if request.method == 'POST':
        destination = request.form.get('destination', '').strip()
        purpose = request.form.get('purpose', '').strip()
        associates = request.form.get('associates', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        vehicle_needed = 'yes' if request.form.get('vehicle_needed') else 'no'
        
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
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if db_type == 'sqlite':
                cursor.execute("""
                    INSERT INTO tickets (user_id, division_id, destination, purpose, associates, start_date, end_date, vehicle_needed, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """, (session['user_id'], division_id, destination, purpose, associates, start_date, end_date, vehicle_needed))
            else:
                cursor.execute("""
                    INSERT INTO tickets (user_id, division_id, destination, purpose, associates, start_date, end_date, vehicle_needed, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                """, (session['user_id'], division_id, destination, purpose, associates, start_date, end_date, vehicle_needed))
            
            conn.commit()
            
            flash('Travel request submitted successfully!', 'success')
            return redirect(url_for('tickets.my_tickets'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error creating ticket: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    # Get user's division
    division_name = ''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("SELECT name FROM divisions WHERE id = ?", (division_id,))
        else:
            cursor.execute("SELECT name FROM divisions WHERE id = %s", (division_id,))
        
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
    conn = None
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

        if request.method == 'POST':
            destination = request.form.get('destination', '').strip()
            purpose = request.form.get('purpose', '').strip()
            associates = request.form.get('associates', '').strip()
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            vehicle_needed = 'yes' if request.form.get('vehicle_needed') else 'no'

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
                    SET destination = ?, purpose = ?, associates = ?, start_date = ?, end_date = ?, vehicle_needed = ?
                    WHERE id = ?
                """, (destination, purpose, associates, start_date, end_date, vehicle_needed, ticket_id))
            else:
                cursor.execute("""
                    UPDATE tickets 
                    SET destination = %s, purpose = %s, associates = %s, start_date = %s, end_date = %s, vehicle_needed = %s
                    WHERE id = %s
                """, (destination, purpose, associates, start_date, end_date, vehicle_needed, ticket_id))

            conn.commit()
            flash('Travel request updated successfully!', 'success')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error loading or updating ticket: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    finally:
        if conn:
            conn.close()

    return render_template('tickets/edit.html', ticket=ticket)


@tickets_bp.route('/<int:ticket_id>')
def view(ticket_id):
    """View ticket details"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    db_type = get_db_type()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get ticket with vehicle info
        if db_type == 'sqlite':
            cursor.execute("""
                SELECT t.*, u.full_name as user_name, d.name as division_name,
                       v.name as vehicle_name, v.status as vehicle_status
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                JOIN divisions d ON t.division_id = d.id
                LEFT JOIN vehicles v ON t.vehicle_assigned = v.name
                WHERE t.id = ?
            """, (ticket_id,))
        else:
            cursor.execute("""
                SELECT t.*, u.full_name as user_name, d.name as division_name,
                       v.name as vehicle_name, v.status as vehicle_status
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                JOIN divisions d ON t.division_id = d.id
                LEFT JOIN vehicles v ON t.vehicle_assigned = v.name
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
        
        # Get available vehicles for admin
        available_vehicles = get_available_vehicles() if session.get('role') == 'admin' else []
        
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
        
        # Convert dates
        if ticket.get('start_date') and isinstance(ticket.get('start_date'), str):
            ticket['start_date'] = datetime.strptime(ticket['start_date'], '%Y-%m-%d').date()
        if ticket.get('end_date') and isinstance(ticket.get('end_date'), str):
            ticket['end_date'] = datetime.strptime(ticket['end_date'], '%Y-%m-%d').date()
        
        for approval in approvals:
            if approval.get('created_at') and isinstance(approval.get('created_at'), str):
                approval['created_at'] = datetime.strptime(approval['created_at'], '%Y-%m-%d %H:%M:%S')
            
    except Exception as e:
        flash(f'Error loading ticket: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('tickets/view.html', ticket=ticket, approvals=approvals, available_vehicles=available_vehicles)


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
    
    conn = None
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
        
        # Prevent users from approving their own tickets
        if ticket['user_id'] == session['user_id']:
            flash('You cannot approve your own ticket.', 'danger')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
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
        
        flash(f'Ticket #{ticket_id} approved successfully!', 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error approving ticket: {str(e)}', 'danger')
    finally:
        if conn:
            conn.close()
    
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
    
    conn = None
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
        
        if ticket['user_id'] == session['user_id']:
            flash('You cannot reject your own ticket.', 'danger')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))

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
        
        flash(f'Ticket #{ticket_id} has been rejected', 'warning')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error rejecting ticket: {str(e)}', 'danger')
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))


@tickets_bp.route('/<int:ticket_id>/assign_vehicle', methods=['POST'])
def assign_vehicle(ticket_id):
    """Assign vehicle to approved ticket (admin only)"""
    if not require_login() or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    vehicle_assigned = request.form.get('vehicle_assigned', '').strip()
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    if not vehicle_assigned:
        flash('Vehicle selection is required', 'danger')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("UPDATE tickets SET vehicle_assigned = ? WHERE id = ? AND status = 'approved'", (vehicle_assigned, ticket_id))
            rows_affected = cursor.rowcount
        else:
            cursor.execute("UPDATE tickets SET vehicle_assigned = %s WHERE id = %s AND status = 'approved'", (vehicle_assigned, ticket_id))
            rows_affected = cursor.rowcount
        
        conn.commit()
        
        if rows_affected > 0:
            flash(f'Vehicle {vehicle_assigned} assigned to ticket #{ticket_id}', 'success')
        else:
            flash('Ticket not found or not approved', 'danger')
            
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error assigning vehicle: {str(e)}', 'danger')
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

