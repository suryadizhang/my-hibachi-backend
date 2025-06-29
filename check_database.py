#!/usr/bin/env python3
"""
Check database schema and tables
"""
import sqlite3
from pathlib import Path

def check_database():
    db_file = Path(__file__).parent / "mh-bookings.db"
    
    if not db_file.exists():
        print("Database file does not exist!")
        return
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Check all tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    
    print("Database tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check users table if it exists
    if any(table[0] == 'users' for table in tables):
        print("\nUsers table schema:")
        c.execute("PRAGMA table_info(users)")
        columns = c.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("\nUsers table does not exist!")
    
    conn.close()

if __name__ == "__main__":
    check_database()
