import sqlite3

# Connect to the database
conn = sqlite3.connect('cityhall.db')
cursor = conn.cursor()

# Check current columns
cursor.execute('PRAGMA table_info(tickets)')
columns = cursor.fetchall()
print('Current columns:', [col[1] for col in columns])

# Add vehicle_needed column if missing
column_names = [col[1] for col in columns]
if 'vehicle_needed' not in column_names:
    cursor.execute('ALTER TABLE tickets ADD COLUMN vehicle_needed VARCHAR(10) DEFAULT "no"')
    print('Added vehicle_needed column')
if 'vehicle_assigned' not in column_names:
    cursor.execute('ALTER TABLE tickets ADD COLUMN vehicle_assigned VARCHAR(100)')
    print('Added vehicle_assigned column')

conn.commit()
conn.close()
print('Done!')
