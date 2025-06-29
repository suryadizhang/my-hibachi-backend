import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

# Check if admin table exists
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="admin_users"')
result = cursor.fetchone()
print('Admin table exists:', bool(result))

if result:
    cursor.execute('SELECT username FROM admin_users')
    admins = cursor.fetchall()
    print('Admins:', [admin[0] for admin in admins])
else:
    print('No admin table found')

conn.close()
