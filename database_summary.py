import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

print("=== MY HIBACHI NEWSLETTER DATABASE SUMMARY ===")
print()

# Total count
cursor.execute('SELECT COUNT(*) FROM company_newsletter')
total = cursor.fetchone()[0]
print(f"📊 TOTAL CUSTOMERS: {total}")
print()

# Field completeness analysis
fields = [
    ('name', 'Names'),
    ('phone', 'Phone Numbers'),
    ('email', 'Email Addresses'),
    ('address', 'Addresses'),
    ('city', 'Cities'),
    ('state', 'States'),
    ('zipcode', 'ZIP Codes'),
    ('last_activity_date', 'Last Order Details'),
    ('geographic_region', 'Geographic Regions'),
    ('booking_history', 'Booking History')
]

print("📋 FIELD COMPLETENESS:")
for field, label in fields:
    cursor.execute(f'SELECT COUNT(*) FROM company_newsletter WHERE {field} IS NOT NULL AND {field} != ""')
    count = cursor.fetchone()[0]
    percentage = (count / total) * 100
    print(f"  ✓ {label}: {count}/{total} ({percentage:.1f}%)")

print()

# Sample data with all fields
print("📋 SAMPLE CUSTOMER RECORDS:")
cursor.execute('SELECT * FROM company_newsletter WHERE source = "CSV Import" LIMIT 3')
rows = cursor.fetchall()

for i, row in enumerate(rows, 1):
    print(f"\n--- Customer {i} ---")
    print(f"Name: {row[1]}")
    print(f"Phone: {row[2]}")
    print(f"Email: {row[3] if row[3] else 'Not provided'}")
    print(f"Address: {row[4]}")
    print(f"City: {row[5]}")
    print(f"State: {row[9]}")
    print(f"ZIP Code: {row[6]}")
    print(f"Last Order Date: {row[7]}")
    print(f"Geographic Region: {row[10]}")
    print(f"Booking History: {row[11] if row[11] else 'None'}")

# Geographic distribution
print("\n🗺️  GEOGRAPHIC DISTRIBUTION:")
cursor.execute('SELECT state, COUNT(*) FROM company_newsletter WHERE state IS NOT NULL GROUP BY state ORDER BY COUNT(*) DESC')
states = cursor.fetchall()
for state, count in states:
    print(f"  {state}: {count} customers")

print("\n🌍 REGIONAL DISTRIBUTION:")
cursor.execute('SELECT geographic_region, COUNT(*) FROM company_newsletter WHERE geographic_region IS NOT NULL GROUP BY geographic_region ORDER BY COUNT(*) DESC')
regions = cursor.fetchall()
for region, count in regions:
    print(f"  {region}: {count} customers")

# Contact info analysis
print("\n📞 CONTACT INFORMATION:")
cursor.execute('SELECT COUNT(*) FROM company_newsletter WHERE email IS NOT NULL AND email != "unknown" AND email != ""')
valid_emails = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM company_newsletter WHERE phone IS NOT NULL AND phone != ""')
valid_phones = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM company_newsletter WHERE (email IS NOT NULL AND email != "unknown" AND email != "") OR (phone IS NOT NULL AND phone != "")')
contactable = cursor.fetchone()[0]

print(f"  Valid Email Addresses: {valid_emails}")
print(f"  Valid Phone Numbers: {valid_phones}")
print(f"  Contactable Customers: {contactable} ({(contactable/total)*100:.1f}%)")

print("\n✅ CONCLUSION:")
print("The database contains all the requested fields:")
print("  ✓ Name")
print("  ✓ Address (full address)")
print("  ✓ Phone Number")
print("  ✓ Last Order Details (date)")
print("  ✓ Email Address (when provided)")
print("  ✓ City")
print("  ✓ ZIP Code")
print("  ✓ State")
print("  ✓ Geographic Region")
print("  ✓ Booking History")

conn.close()
