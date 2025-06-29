import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

# Check total count
cursor.execute('SELECT COUNT(*) FROM company_newsletter')
total = cursor.fetchone()[0]
print(f'Total customers: {total}')

# Show sample data with all fields
cursor.execute('SELECT * FROM company_newsletter LIMIT 5')
rows = cursor.fetchall()
print('\nSample data (first 5 records):')
for i, row in enumerate(rows):
    print(f'\nRecord {i+1}:')
    print(f'  ID: {row[0]}')
    print(f'  Name: {row[1]}')
    print(f'  Phone: {row[2]}')
    print(f'  Email: {row[3]}')
    print(f'  Address: {row[4]}')
    print(f'  City: {row[5]}')
    print(f'  Zipcode: {row[6]}')
    print(f'  Last Activity: {row[7]}')
    print(f'  Source: {row[8]}')
    print(f'  State: {row[9]}')
    print(f'  Geographic Region: {row[10]}')
    print(f'  Booking History: {row[11]}')
    print(f'  Created At: {row[12]}')

# Check distribution by state
print('\n--- Distribution by State ---')
cursor.execute('SELECT state, COUNT(*) FROM company_newsletter GROUP BY state ORDER BY COUNT(*) DESC')
states = cursor.fetchall()
for state, count in states:
    print(f'{state}: {count} customers')

# Check distribution by region
print('\n--- Distribution by Geographic Region ---')
cursor.execute('SELECT geographic_region, COUNT(*) FROM company_newsletter GROUP BY geographic_region ORDER BY COUNT(*) DESC')
regions = cursor.fetchall()
for region, count in regions:
    print(f'{region}: {count} customers')

# Check customers with email addresses
print('\n--- Email Addresses ---')
cursor.execute('SELECT COUNT(*) FROM company_newsletter WHERE email IS NOT NULL AND email != "unknown"')
email_count = cursor.fetchone()[0]
print(f'Customers with valid email addresses: {email_count}')

if email_count > 0:
    cursor.execute('SELECT name, email FROM company_newsletter WHERE email IS NOT NULL AND email != "unknown" LIMIT 5')
    email_customers = cursor.fetchall()
    print('Sample customers with emails:')
    for name, email in email_customers:
        print(f'  {name}: {email}')

conn.close()
