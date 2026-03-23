"""
Script to initialize MySQL database for City ENRO Travel Request System
"""
import pymysql
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'city_enro_travel')

def init_db():
    """Initialize database and create tables"""
    print("Starting database initialization...")
    
    try:
        # First connect without database to create it
        print(f"Connecting to MySQL at {MYSQL_HOST}...")
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database
        print(f"Creating database '{MYSQL_DATABASE}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        conn.close(
        
        # Now connect to the database
        print(f"Connecting to database '{MYSQL_DATABASE}'...")
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        # Create divisions table
        print("Creating divisions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS divisions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)
        
        # Create users table
        print("Creating users table...")
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
        print("Creating tickets table...")
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
                vehicle_needed VARCHAR(10) DEFAULT 'no',
                vehicle_assigned VARCHAR(100),
                status ENUM('pending', 'director_approved', 'approved', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (division_id) REFERENCES divisions(id)
            )
        """)
        
        # Create approvals table
        print("Creating approvals table...")
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
        print("Inserting default divisions...")
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
            print(f"Inserted {len(divisions)} divisions")
        
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
            print("Inserted default admin user (username: admin, password: admin123)")
        
        # Insert sample director and final authorizer users
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'director'")
        if cursor.fetchone()[0] == 0:
            bcrypt = Bcrypt()
            
            # Director 1
            hashed = bcrypt.generate_password_hash('director123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, division_id, full_name) VALUES (%s, %s, %s, %s, %s)",
                ('director1', hashed, 'director', 1, 'John Director')
            )
            
            # Director 2
            hashed = bcrypt.generate_password_hash('director123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, division_id, full_name) VALUES (%s, %s, %s, %s, %s)",
                ('director2', hashed, 'director', 2, 'Jane Director')
            )
            print("Inserted sample director users")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'final_authorizer'")
        if cursor.fetchone()[0] == 0:
            bcrypt = Bcrypt()
            hashed = bcrypt.generate_password_hash('authorizer123').decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                ('authorizer', hashed, 'final_authorizer', 'Chief Authorizer')
            )
            print("Inserted sample final authorizer user")
        
        conn.commit()
        conn.close()
        
        print("\n" + "="*50)
        print("Database initialized successfully!")
        print("="*50)
        print("\nDefault users created:")
        print("  - Admin: username='admin', password='admin123', role='admin'")
        print("  - Director 1: username='director1', password='director123', role='director'")
        print("  - Director 2: username='director2', password='director123', role='director'")
        print("  - Final Authorizer: username='authorizer', password='authorizer123', role='final_authorizer'")
        print("\nTo create employees, use the registration page at /auth/register")
        
    except pymysql.err.OperationalError as e:
        print(f"\nMySQL Connection Error: {e}")
        print("\nPlease check:")
        print("  1. MySQL service is running")
        print("  2. Username and password are correct")
        print("  3. MySQL is accessible on localhost")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_db()

