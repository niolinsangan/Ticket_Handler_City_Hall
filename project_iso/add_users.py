"""Script to add director and final_authorizer users to existing SQLite database"""
import sqlite3
from flask_bcrypt import Bcrypt

db_path = "c:/Users/Niiyyoooww/Desktop/CITY_HALL_ASSIGNMENT/project_dir/Ticket_Handler_City_Hall/project_iso/cityhall.db"
bcrypt = Bcrypt()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if director users exist
cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'director'")
director_count = cursor.fetchone()[0]
print(f"Current director count: {director_count}")

if director_count == 0:
    # Director 1
    hashed = bcrypt.generate_password_hash('director123').decode('utf-8')
    cursor.execute(
        "INSERT INTO users (username, password, role, division_id, full_name) VALUES (?, ?, ?, ?, ?)",
        ('director1', hashed, 'director', 1, 'John Director')
    )
    print("Added director1")
    
    # Director 2
    hashed = bcrypt.generate_password_hash('director123').decode('utf-8')
    cursor.execute(
        "INSERT INTO users (username, password, role, division_id, full_name) VALUES (?, ?, ?, ?, ?)",
        ('director2', hashed, 'director', 2, 'Jane Director')
    )
    print("Added director2")

# Check if final_authorizer exists
cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'final_authorizer'")
authorizer_count = cursor.fetchone()[0]
print(f"Current final_authorizer count: {authorizer_count}")

if authorizer_count == 0:
    hashed = bcrypt.generate_password_hash('authorizer123').decode('utf-8')
    cursor.execute(
        "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
        ('authorizer', hashed, 'final_authorizer', 'Chief Authorizer')
    )
    print("Added authorizer")

conn.commit()

# Verify
cursor.execute("SELECT username, role, full_name FROM users")
users = cursor.fetchall()
print("\nAll users in database:")
for user in users:
    print(f"  - {user[0]}: {user[1]} ({user[2]})")

conn.close()
print("\nDone!")
