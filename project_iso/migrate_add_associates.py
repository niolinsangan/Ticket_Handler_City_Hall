"""
Migration script to add associates, vehicle_needed, and vehicle_assigned columns to SQLite database
"""
import sqlite3
import os
from config import Config

def migrate():
    """Add associates, vehicle_needed, and vehicle_assigned columns to tickets table"""
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
    print(f"Current columns: {columns}")
    
    # Add associates column if not exists
    if 'associates' not in columns:
        print("Adding 'associates' column...")
        cursor.execute("ALTER TABLE tickets ADD COLUMN associates TEXT")
        print("Added 'associates' column")
    else:
        print("'associates' column already exists")
    
    # Add vehicle_needed column if not exists
    if 'vehicle_needed' not in columns:
        print("Adding 'vehicle_needed' column...")
        cursor.execute("ALTER TABLE tickets ADD COLUMN vehicle_needed VARCHAR(10) DEFAULT 'no'")
        print("Added 'vehicle_needed' column")
    else:
        print("'vehicle_needed' column already exists")
    
    # Add vehicle_assigned column if not exists
    if 'vehicle_assigned' not in columns:
        print("Adding 'vehicle_assigned' column...")
        cursor.execute("ALTER TABLE tickets ADD COLUMN vehicle_assigned VARCHAR(100)")
        print("Added 'vehicle_assigned' column")
    else:
        print("'vehicle_assigned' column already exists")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
