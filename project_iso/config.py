import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Database choice: 'mysql' or 'sqlite'
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE')
    
    # MySQL URI format
    MYSQL_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
    
    # SQLite Configuration - stores in project directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE = os.path.join(BASE_DIR, 'cityhall.db')
    
    # Session config
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_TYPE = 'sqlite'  # Use SQLite for local development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'mysql')


class SQLiteConfig(Config):
    """SQLite configuration for Vercel/deployment"""
    DEBUG = True
    DATABASE_TYPE = 'sqlite'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'sqlite': SQLiteConfig,
    'default': DevelopmentConfig
}

