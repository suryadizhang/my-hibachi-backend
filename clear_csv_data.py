import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM company_newsletter WHERE source = "CSV Import"')
conn.commit()
cursor.execute('SELECT COUNT(*) FROM company_newsletter')
remaining = cursor.fetchone()[0]
print(f'Cleared CSV import data. Remaining customers: {remaining}')
conn.close()
