from flask import Blueprint, render_template, redirect, url_for, flash, session
import sqlite3
import pymysql
from config import Config

main_bp = Blueprint('main', __name__)


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


@main_bp.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
def dashboard():
    """User dashboard - role-based view"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_role = session.get('role')
    user_name = session.get('full_name', 'User')
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    # Get stats based on role
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_role == 'employee':
            # Employee: show their own stats
            if db_type == 'sqlite':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'director_approved' THEN 1 ELSE 0 END) as director_approved,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                    FROM tickets 
                    WHERE user_id = ?
                """, (session['user_id'],))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'director_approved' THEN 1 ELSE 0 END) as director_approved,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                    FROM tickets 
                    WHERE user_id = %s
                """, (session['user_id'],))
            
            stats = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
            
            # Get user's recent tickets
            if db_type == 'sqlite':
                cursor.execute("""
                    SELECT t.*, d.name as division_name
                    FROM tickets t
                    JOIN divisions d ON t.division_id = d.id
                    WHERE t.user_id = ?
                    ORDER BY t.created_at DESC
                    LIMIT 5
                """, (session['user_id'],))
            else:
                cursor.execute("""
                    SELECT t.*, d.name as division_name
                    FROM tickets t
                    JOIN divisions d ON t.division_id = d.id
                    WHERE t.user_id = %s
                    ORDER BY t.created_at DESC
                    LIMIT 5
                """, (session['user_id'],))
            
            rows = cursor.fetchall()
            recent_tickets = [dict_from_row(row) for row in rows] if db_type == 'sqlite' else cursor.fetchall()
            
        else:
            # Director/Final Authorizer: show all stats
            if db_type == 'sqlite':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'director_approved' THEN 1 ELSE 0 END) as director_approved,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                    FROM tickets
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'director_approved' THEN 1 ELSE 0 END) as director_approved,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                    FROM tickets
                """)
            
            stats = dict_from_row(cursor.fetchone()) if db_type == 'sqlite' else cursor.fetchone()
            
            # Get all recent tickets
            if db_type == 'sqlite':
                cursor.execute("""
                    SELECT t.*, u.full_name as user_name, d.name as division_name
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    JOIN divisions d ON t.division_id = d.id
                    ORDER BY t.created_at DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT t.*, u.full_name as user_name, d.name as division_name
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    JOIN divisions d ON t.division_id = d.id
                    ORDER BY t.created_at DESC
                    LIMIT 10
                """)
            
            rows = cursor.fetchall()
            recent_tickets = [dict_from_row(row) for row in rows] if db_type == 'sqlite' else cursor.fetchall()
        
        conn.close()
        
        # Convert Decimal
        if stats:
            for key in stats:
                if stats[key] is None:
                    stats[key] = 0
        
        for ticket in recent_tickets:
            if ticket.get('estimated_cost'):
                ticket['estimated_cost'] = float(ticket['estimated_cost'])
        
    except Exception as e:
        stats = {'total': 0, 'pending': 0, 'director_approved': 0, 'approved': 0, 'rejected': 0}
        recent_tickets = []
        flash(f'Error loading dashboard: {str(e)}', 'danger')
    
    return render_template('main/dashboard.html', 
                         stats=stats, 
                         recent_tickets=recent_tickets,
                         user_name=user_name,
                         user_role=user_role)


@main_bp.route('/divisions')
def divisions():
    """View all divisions"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM divisions ORDER BY name")
            rows = cursor.fetchall()
            divisions = [dict_from_row(row) for row in rows]
        else:
            cursor.execute("SELECT * FROM divisions ORDER BY name")
            divisions = cursor.fetchall()
        
        conn.close()
    except Exception as e:
        flash(f'Error loading divisions: {str(e)}', 'danger')
        divisions = []
    
    return render_template('main/divisions.html', divisions=divisions)

