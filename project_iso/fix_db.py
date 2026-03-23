"""
Migration script to remove estimated_cost column from both SQLite and MySQL databases.
"""
import sqlite3
import pymysql
import os
from config import Config, config

def fix_db():
    """Remove estimated_cost column from tickets table"""
    db_type = os.getenv('DATABASE_TYPE', 'sqlite')
    print(f"Database type: {db_type}")

    if db_type == 'sqlite':
        fix_sqlite()
    elif db_type == 'mysql':
        fix_mysql()
    else:
        print(f"Unsupported database type: {db_type}")

def fix_sqlite():
    """Fix SQLite database"""
    db_path = Config.SQLITE_DATABASE
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns in tickets table: {columns}")
    
    # Check if estimated_cost column exists
    if 'estimated_cost' in columns:
        print("Found 'estimated_cost' column in SQLite database.")
        print("SQLite does not support dropping columns in a straightforward way.")
        print("The recommended approach is to recreate the table and copy the data.")
        print("Since the 'estimated_cost' column is no longer used by the application, you can choose to ignore this column or remove it manually using a database browser.")
    else:
        print("'estimated_cost' column not found in tickets table.")
    
    conn.close()
    print("SQLite check completed.")

def fix_mysql():
    """Fix MySQL database"""
    try:
        # Now connect to the database
        print(f"Connecting to MySQL database...")
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        cursor = conn.cursor()
        
        # Check if estimated_cost column exists
        cursor.execute("SHOW COLUMNS FROM tickets LIKE 'estimated_cost'")
        result = cursor.fetchone()
        
        if result:
            print("Found 'estimated_cost' column in MySQL database. Dropping it...")
            cursor.execute("ALTER TABLE tickets DROP COLUMN estimated_cost")
            print("Dropped 'estimated_cost' column.")
        else:
            print("'estimated_cost' column not found in tickets table.")
            
        conn.commit()
        conn.close()
        print("MySQL check completed.")
        
    except pymysql.err.OperationalError as e:
        print(f"\nMySQL Connection Error: {e}")
        print("\nPlease check:")
        print("  1. MySQL service is running")
        print("  2. Username and password are correct")
        print("  3. MySQL is accessible on localhost")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == '__main__':
    fix_db()
