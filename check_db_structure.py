#!/usr/bin/env python3
"""Check database structure"""

import sqlite3

def check_db_structure():
    conn = sqlite3.connect('mh-bookings.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in mh-bookings.db:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        
        if table[0] in ['users', 'admins']:
            print(f"  Columns in {table[0]}:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # Show sample data
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
            rows = cursor.fetchall()
            print(f"  Sample data ({len(rows)} rows):")
            for row in rows:
                print(f"    {row}")
            print()
    
    conn.close()

if __name__ == "__main__":
    check_db_structure()
