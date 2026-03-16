import sqlite3
import pymysql
from config import Config
from db import get_db_connection, get_db_type, dict_from_row

def get_db_type():
    return getattr(Config, 'DATABASE_TYPE', 'sqlite')

def migrate():
    db_type = get_db_type()
    
    conn = get_db_connection() if 'get_db_connection' in globals() else None
    if not conn:
        if db_type == 'sqlite':
            db_path = getattr(Config, 'SQLITE_DATABASE', 'cityhall.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        else:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor
            )
    
    cursor = conn.cursor()
    
    # Create vehicles table if not exists
    if db_type == 'sqlite':
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                vehicle_type VARCHAR(50) DEFAULT 'car',
                status VARCHAR(20) DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                vehicle_type VARCHAR(50) DEFAULT 'car',
                status ENUM('available', 'assigned', 'maintenance') DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    # Seed cars if not exist
    cars = ['car 1', 'car 2', 'car 3', 'car 4']
    for car in cars:
        if db_type == 'sqlite':
            cursor.execute("SELECT id FROM vehicles WHERE name = ?", (car,))
        else:
            cursor.execute("SELECT id FROM vehicles WHERE name = %s", (car,))
        
        if not cursor.fetchone():
            if db_type == 'sqlite':
                cursor.execute("INSERT INTO vehicles (name) VALUES (?)", (car,))
            else:
                cursor.execute("INSERT INTO vehicles (name) VALUES (%s)", (car,))
    
    conn.commit()
    conn.close()
    print("Migration complete: vehicles table added with cars 1-4.")

if __name__ == '__main__':
    migrate()

