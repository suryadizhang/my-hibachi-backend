#!/usr/bin/env python3
"""
Check waitlist table in the main database.
"""
import sqlite3
import sys

def check_waitlist_table():
    """Check if waitlist table exists and examine its structure."""
    print("=== CHECKING WAITLIST TABLE ===")
    
    try:
        with sqlite3.connect('mh-bookings.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Check if waitlist table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='waitlist'")
            table_exists = c.fetchone()
            
            if table_exists:
                print("✅ Waitlist table exists")
                
                # Get table schema
                c.execute("PRAGMA table_info(waitlist)")
                columns = c.fetchall()
                print("\n📋 Waitlist table schema:")
                for col in columns:
                    pk_info = " (PRIMARY KEY)" if col[5] else ""
                    null_info = " NOT NULL" if col[3] else ""
                    print(f"   {col[1]} {col[2]}{null_info}{pk_info}")
                
                # Get count of waitlist entries
                c.execute("SELECT COUNT(*) FROM waitlist")
                count = c.fetchone()[0]
                print(f"\n📊 Total waitlist entries: {count}")
                
                if count > 0:
                    # Show sample entries
                    c.execute("SELECT * FROM waitlist ORDER BY created_at LIMIT 5")
                    entries = c.fetchall()
                    print("\n📝 Sample waitlist entries:")
                    for i, entry in enumerate(entries, 1):
                        entry_dict = dict(entry)
                        print(f"   Entry {i}:")
                        for key, value in entry_dict.items():
                            print(f"      {key}: {value}")
                        print()
            else:
                print("❌ Waitlist table does not exist")
                
                # Check if we need to create it
                print("\n🔧 Creating waitlist table...")
                c.execute("""
                    CREATE TABLE IF NOT EXISTS waitlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        email TEXT NOT NULL,
                        preferred_date TEXT NOT NULL,
                        preferred_time TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✅ Waitlist table created")
                
            # List all tables in the database
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            print("\n📋 All tables in mh-bookings.db:")
            for table in tables:
                print(f"   - {table[0]}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
        
    print("=== WAITLIST CHECK COMPLETE ===")
    return True

if __name__ == "__main__":
    success = check_waitlist_table()
    sys.exit(0 if success else 1)
