#!/usr/bin/env python3
"""
Create missing bookings table in the database
"""
import sqlite3
import sys
import os


def create_bookings_table():
    """Create the bookings table if it doesn't exist"""
    try:
        # Connect to database
        db_path = 'mh-bookings.db'
        if not os.path.exists(db_path):
            print(f"Warning: Database file {db_path} does not exist. "
                  f"Creating new database.")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create missing bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                city TEXT,
                zipcode TEXT,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                contact_preference TEXT DEFAULT 'email',
                status TEXT DEFAULT 'pending',
                deposit_confirmed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verify table was created
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='bookings'"
        )
        result = cursor.fetchone()
        
        if result:
            print("✅ Bookings table created successfully")
            
            # Check if table has any data
            cursor.execute("SELECT COUNT(*) FROM bookings")
            count = cursor.fetchone()[0]
            print(f"📊 Bookings table contains {count} records")
        else:
            print("❌ Failed to create bookings table")
            return False
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating bookings table: {e}")
        return False


if __name__ == "__main__":
    success = create_bookings_table()
    sys.exit(0 if success else 1)
