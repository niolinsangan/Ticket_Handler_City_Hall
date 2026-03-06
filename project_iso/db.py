"""
Database helper module - supports both MySQL and SQLite
"""
import sqlite3
import pymysql
from flask import current_app

# Track the current database type
_db_type = 'sqlite'

def get_db_type():
    """Get the current database type from app config"""
    try:
        from flask import has_request_context, request
        if has_request_context() and hasattr(current_app, 'config'):
            return current_app.config.get('DATABASE_TYPE', 'sqlite')
    except:
        pass
    return 'sqlite'


def get_db_connection():
    """Get database connection based on configuration"""
    db_type = get_db_type()
    
    if db_type == 'sqlite':
        return get_sqlite_connection()
    else:
        return get_mysql_connection()


def get_sqlite_connection():
    """Get SQLite database connection"""
    import os
    from config import Config
    
    # Get the database path from config
    db_path = getattr(Config, 'SQLITE_DATABASE', 'cityhall.db')
    
    # If running in app context, use the app's config
    try:
        if hasattr(current_app, 'config'):
            db_path = current_app.config.get('SQLITE_DATABASE', db_path)
    except:
        pass
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_mysql_connection():
    """Get MySQL database connection"""
    from config import Config
    
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )


def dict_from_row(row):
    """Convert a sqlite3.Row to a dictionary"""
    if row is None:
        return None
    if hasattr(row, 'keys'):
        return dict(zip(row.keys(), row))
    return row


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Execute a query and return results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    db_type = get_db_type()
    
    try:
        if db_type == 'sqlite':
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        else:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        
        if commit:
            conn.commit()
            result = cursor.lastrowid
        elif fetch_one:
            result = dict_from_row(cursor.fetchone())
        elif fetch_all:
            rows = cursor.fetchall()
            result = [dict_from_row(row) for row in rows]
        else:
            result = None
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        raise e

