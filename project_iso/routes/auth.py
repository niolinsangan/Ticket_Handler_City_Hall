from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_bcrypt import Bcrypt
import sqlite3
import pymysql
from config import Config

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()


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


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('auth/login.html', layout='minimal')
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
            
            if db_type == 'sqlite':
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                user = dict_from_row(row) if row else None
            else:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
            
            if user and bcrypt.check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                session['division_id'] = user.get('division_id')
                
                flash(f'Welcome, {user["full_name"]}!', 'success')
                
                # Redirect based on role
                if user['role'] == 'employee':
                    return redirect(url_for('main.dashboard'))
                elif user['role'] in ['director', 'final_authorizer', 'admin']:
                    return redirect(url_for('tickets.all_tickets'))
                else:
                    return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid username or password', 'danger')
                
        except Exception as e:
            flash(f'Login error: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template('auth/login.html', layout='minimal')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration disabled - Admin only"""
    flash('User registration is disabled. Contact your admin officer to create an account.', 'warning')
    return redirect(url_for('auth.login'))

