#!/usr/bin/env python3
import sqlite3

def test_database():
    conn = sqlite3.connect('mh-bookings.db')
    c = conn.cursor()
    
    # Check what tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = c.fetchall()
    print('Tables in database:', [table[0] for table in tables])
    
    # Check activity_logs table
    try:
        c.execute('SELECT COUNT(*) FROM activity_logs')
        count = c.fetchone()[0]
        print(f'Activity logs table exists with {count} records')
        
        # Check table schema
        c.execute("PRAGMA table_info(activity_logs)")
        columns = c.fetchall()
        print('Activity logs columns:', [col[1] for col in columns])
        
    except Exception as e:
        print(f'Error checking activity_logs: {e}')
    
    conn.close()

if __name__ == "__main__":
    test_database()
