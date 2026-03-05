import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import config
import pymysql

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
    """Initialize database and create tables"""
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
                'Administration', 'Finance', 'Operations', 'Human Resources',
                'IT Services', 'Legal', 'Public Relations', 'Infrastructure'
            ]
            for div in divisions:
                cursor.execute("INSERT INTO divisions (name) VALUES (%s)", (div,))
        
        # Insert default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt()
            hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                ('admin', hashed, 'admin', 'System Administrator')
            )
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Database initialization error: {e}")


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
