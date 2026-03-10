import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import config

# Initialize extensions
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.tickets import tickets_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    
    # Create database tables if not exist
    init_db(app)
    
    return app


def init_db(app):
    """Initialize database and create tables - supports both MySQL and SQLite"""
    db_type = app.config.get('DATABASE_TYPE', 'sqlite')
    
    if db_type == 'sqlite':
        init_sqlite_db(app)
    else:
        init_mysql_db(app)


def init_sqlite_db(app):
    """Initialize SQLite database"""
    import sqlite3
    from flask_bcrypt import Bcrypt
    
    db_path = app.config['SQLITE_DATABASE']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create divisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL
        )
    """)
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            division_id INTEGER,
            full_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (division_id) REFERENCES divisions(id)
        )
    """)
    
    # Create tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            division_id INTEGER NOT NULL,
            destination VARCHAR(200) NOT NULL,
            purpose TEXT NOT NULL,
            associates TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            estimated_cost DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (division_id) REFERENCES divisions(id)
        )
    """)
    
    # Create approvals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            approver_id INTEGER NOT NULL,
            level VARCHAR(50) NOT NULL,
            action VARCHAR(50) NOT NULL,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id),
            FOREIGN KEY (approver_id) REFERENCES users(id)
        )
    """)
    
    # Insert default divisions
    cursor.execute("SELECT COUNT(*) FROM divisions")
    if cursor.fetchone()[0] == 0:
        divisions = [
            'Forestry Management Services Division',
            'Wildlife Management Services Division',
            'Protected Area Management Division',
            'Mines and Geosciences Management Service Division',
            'Land Management Services Division',
            'Environmental Management Services Division',
            'Environmental Law Enforcement Division',
            'Administrative Management Services Division'
        ]
        for div in divisions:
            cursor.execute("INSERT INTO divisions (name) VALUES (?)", (div,))
    
    # Insert default admin user if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        bcrypt_instance = Bcrypt()
        hashed = bcrypt_instance.generate_password_hash('admin123').decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
            ('admin', hashed, 'admin', 'System Administrator')
        )
    
    # Insert default director users if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'director'")
    if cursor.fetchone()[0] == 0:
        bcrypt_instance = Bcrypt()
        # Director 1
        hashed = bcrypt_instance.generate_password_hash('director123').decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, password, role, division_id, full_name) VALUES (?, ?, ?, ?, ?)",
            ('director1', hashed, 'director', 1, 'John Director')
        )
        # Director 2
        hashed = bcrypt_instance.generate_password_hash('director123').decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, password, role, division_id, full_name) VALUES (?, ?, ?, ?, ?)",
            ('director2', hashed, 'director', 2, 'Jane Director')
        )
    
    # Insert default final authorizer user if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'final_authorizer'")
    if cursor.fetchone()[0] == 0:
        bcrypt_instance = Bcrypt()
        hashed = bcrypt_instance.generate_password_hash('authorizer123').decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
            ('authorizer', hashed, 'final_authorizer', 'Chief Authorizer')
        )
    
    conn.commit()
    conn.close()
    print("SQLite database initialized successfully!")
    print("  - Admin: username='admin', password='admin123', role='admin'")
    print("  - Director 1: username='director1', password='director123', role='director'")
    print("  - Director 2: username='director2', password='director123', role='director'")
    print("  - Final Authorizer: username='authorizer', password='authorizer123', role='final_authorizer'")


def init_mysql_db(app):
    """Initialize MySQL database"""
    import pymysql
    
    try:
        # First connect without database to create it
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DATABASE']}")
        conn.close()
        
        # Now connect to the database
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DATABASE']
        )
        cursor = conn.cursor()
        
        # Create divisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS divisions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('employee', 'director', 'final_authorizer', 'admin') NOT NULL,
                division_id INT,
                full_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (division_id) REFERENCES divisions(id)
            )
        """)
        
        # Create tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                division_id INT NOT NULL,
                destination VARCHAR(200) NOT NULL,
                purpose TEXT NOT NULL,
                associates TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                estimated_cost DECIMAL(10, 2) NOT NULL,
                status ENUM('pending', 'director_approved', 'approved', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (division_id) REFERENCES divisions(id)
            )
        """)
        
        # Create approvals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticket_id INT NOT NULL,
                approver_id INT NOT NULL,
                level ENUM('director', 'final') NOT NULL,
                action ENUM('approved', 'rejected') NOT NULL,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                FOREIGN KEY (approver_id) REFERENCES users(id)
            )
        """)
        
        # Insert default divisions
        cursor.execute("SELECT COUNT(*) FROM divisions")
        if cursor.fetchone()[0] == 0:
            divisions = [
                'Forestry Management Services Division',
                'Wildlife Management Services Division',
                'Protected Area Management Division',
                'Mines and Geosciences Management Service Division',
                'Land Management Services Division',
                'Environmental Management Services Division',
                'Environmental Law Enforcement Division',
                'Administrative Management Services Division'
            ]
            for div in divisions:
                cursor.execute("INSERT INTO divisions (name) VALUES (%s)", (div,))
        
# Insert default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            from flask_bcrypt import Bcrypt
            bcrypt_instance = Bcrypt()
            hashed = bcrypt_instance.generate_password_hash('admin123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                ('admin', hashed, 'admin', 'System Administrator')
            )
        
        # Insert default director users if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'director'")
        if cursor.fetchone()[0] == 0:
            from flask_bcrypt import Bcrypt
            bcrypt_instance = Bcrypt()
            # Director 1
            hashed = bcrypt_instance.generate_password_hash('director123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, division_id, full_name) VALUES (%s, %s, %s, %s, %s)",
                ('director1', hashed, 'director', 1, 'John Director')
            )
            # Director 2
            hashed = bcrypt_instance.generate_password_hash('director123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, division_id, full_name) VALUES (%s, %s, %s, %s, %s)",
                ('director2', hashed, 'director', 2, 'Jane Director')
            )
        
        # Insert default final authorizer user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'final_authorizer'")
        if cursor.fetchone()[0] == 0:
            from flask_bcrypt import Bcrypt
            bcrypt_instance = Bcrypt()
            hashed = bcrypt_instance.generate_password_hash('authorizer123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                ('authorizer', hashed, 'final_authorizer', 'Chief Authorizer')
            )
        
        conn.commit()
        conn.close()
        print("MySQL database initialized successfully!")
        print("  - Admin: username='admin', password='admin123', role='admin'")
        print("  - Director 1: username='director1', password='director123', role='director'")
        print("  - Director 2: username='director2', password='director123', role='director'")
        print("  - Final Authorizer: username='authorizer', password='authorizer123', role='final_authorizer'")
        
    except Exception as e:
        print(f"MySQL database initialization error: {e}")


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)

