"""
Migration script to remove 'estimated_cost' column from tickets table if exists
Supports SQLite and MySQL
"""
import sqlite3
import pymysql
from config
