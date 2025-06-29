import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

# Check count
cursor.execute('SELECT COUNT(*) FROM company_newsletter')
count = cursor.fetchone()[0]
print(f'Total rows in company_newsletter: {count}')

# Show sample data if any exists
if count > 0:
    cursor.execute('SELECT * FROM company_newsletter LIMIT 3')
    rows = cursor.fetchall()
    print('\nSample data:')
    for row in rows:
        print(row)
else:
    print('No data found in company_newsletter table')

conn.close()
