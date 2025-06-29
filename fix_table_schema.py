import sqlite3

conn = sqlite3.connect('mh-bookings.db')
cursor = conn.cursor()

# Backup existing data
cursor.execute("CREATE TEMPORARY TABLE newsletter_backup AS SELECT * FROM company_newsletter")

# Drop and recreate table without UNIQUE constraint
cursor.execute("DROP TABLE company_newsletter")
cursor.execute("""
    CREATE TABLE company_newsletter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        city TEXT,
        zipcode TEXT,
        last_activity_date TEXT,
        source TEXT,
        state TEXT,
        geographic_region TEXT,
        booking_history TEXT,
        created_at TEXT
    )
""")

# Restore data
cursor.execute("INSERT INTO company_newsletter SELECT * FROM newsletter_backup")
cursor.execute("DROP TABLE newsletter_backup")

conn.commit()
print("✓ Table recreated without UNIQUE constraint on email")

# Check count
cursor.execute("SELECT COUNT(*) FROM company_newsletter")
count = cursor.fetchone()[0]
print(f"Restored {count} existing customers")

conn.close()
