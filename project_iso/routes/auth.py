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
    """User registration (employees only)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        division_id = request.form.get('division_id')
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if not full_name:
            errors.append('Full name is required')
        if not division_id:
            errors.append('Division selection is required')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
            
            # Check if username exists
            if db_type == 'sqlite':
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            else:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            
            if cursor.fetchone():
                flash('Username already exists', 'danger')
                conn.close()
                return redirect(url_for('auth.register'))
            
            # Hash password and create user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            if db_type == 'sqlite':
                cursor.execute(
                    "INSERT INTO users (username, password, role, division_id, full_name) VALUES (?, ?, ?, ?, ?)",
                    (username, hashed_password, 'employee', division_id, full_name)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (username, password, role, division_id, full_name) VALUES (%s, %s, %s, %s, %s)",
                    (username, hashed_password, 'employee', division_id, full_name)
                )
            
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'danger')
    
    # Get divisions for dropdown
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        db_type = getattr(Config, 'DATABASE_TYPE', 'sqlite')
        
        if db_type == 'sqlite':
            cursor.execute("SELECT * FROM divisions ORDER BY name")
            rows = cursor.fetchall()
            divisions = [dict_from_row(row) for row in rows]
        else:
            cursor.execute("SELECT * FROM divisions ORDER BY name")
            divisions = cursor.fetchall()
        
        conn.close()
    except:
        divisions = []
    
    return render_template('auth/register.html', divisions=divisions, layout='minimal')

