#!/usr/bin/env python3
import sqlite3
import os

# Test main database
if os.path.exists('mh-bookings.db'):
    with sqlite3.connect('mh-bookings.db') as conn:
        c = conn.cursor()
        # Check if waitlist table exists
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="waitlist"')
        result = c.fetchone()
        print(f'Waitlist table exists: {bool(result)}')
        
        if result:
            # Check table structure
            c.execute('PRAGMA table_info(waitlist)')
            columns = c.fetchall()
            print('Waitlist table columns:', [col[1] for col in columns])
            
            # Count entries
            c.execute('SELECT COUNT(*) FROM waitlist')
            count = c.fetchone()[0]
            print(f'Waitlist entries: {count}')
        else:
            print('Creating waitlist table...')
            c.execute('''
                CREATE TABLE waitlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    city TEXT,
                    zipcode TEXT,
                    preferred_date TEXT,
                    preferred_time TEXT,
                    party_size INTEGER,
                    created_at TEXT
                )
            ''')
            conn.commit()
            print('Waitlist table created.')
