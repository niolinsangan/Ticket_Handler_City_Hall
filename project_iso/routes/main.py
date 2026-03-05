from flask import Blueprint, render_template, redirect, url_for, flash, session
import pymysql
from config import Config

main_bp = Blueprint('main', __name__)


def get_db_connection():
    """Get MySQL database connection"""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )


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
    
    # Get stats based on role
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_role == 'employee':
            # Employee: show their own stats
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
            
            # Get user's recent tickets
            cursor.execute("""
                SELECT t.*, d.name as division_name
                FROM tickets t
                JOIN divisions d ON t.division_id = d.id
                WHERE t.user_id = %s
                ORDER BY t.created_at DESC
                LIMIT 5
            """, (session['user_id'],))
            recent_tickets = cursor.fetchall()
            
        else:
            # Director/Final Authorizer: show all stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'director_approved' THEN 1 ELSE 0 END) as director_approved,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                FROM tickets
            """)
            
            # Get all recent tickets
            cursor.execute("""
                SELECT t.*, u.full_name as user_name, d.name as division_name
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                JOIN divisions d ON t.division_id = d.id
                ORDER BY t.created_at DESC
                LIMIT 10
            """)
            recent_tickets = cursor.fetchall()
        
        stats = cursor.fetchone()
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
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM divisions ORDER BY name")
        divisions = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f'Error loading divisions: {str(e)}', 'danger')
        divisions = []
    
    return render_template('main/divisions.html', divisions=divisions)
