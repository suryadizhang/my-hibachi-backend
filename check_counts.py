import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM company_newsletter')
total = cursor.fetchone()[0]
print(f'Total customers: {total}')

cursor.execute('SELECT COUNT(*) FROM company_newsletter WHERE source = "CSV Import"')
csv_count = cursor.fetchone()[0]
print(f'CSV imported customers: {csv_count}')

# Check for duplicates by email
cursor.execute('SELECT email, COUNT(*) FROM company_newsletter WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1')
duplicates = cursor.fetchall()
print(f'Duplicate emails: {len(duplicates)}')

if duplicates:
    for email, count in duplicates:
        print(f'  {email}: {count} times')

conn.close()
