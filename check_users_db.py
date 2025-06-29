#!/usr/bin/env python3
"""
Check users database schema
"""
import sqlite3
from pathlib import Path

def check_users_db():
    db_file = Path(__file__).parent / "weekly_databases" / "users.db"
    
    if not db_file.exists():
        print("Users database file does not exist!")
        return
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Check all tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    
    print("Users database tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check users table if it exists
    if any(table[0] == 'users' for table in tables):
        print("\nUsers table schema:")
        c.execute("PRAGMA table_info(users)")
        columns = c.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check existing users
        c.execute("SELECT username, role FROM users")
        users = c.fetchall()
        print(f"\nExisting users ({len(users)}):")
        for user in users:
            print(f"  - {user[0]} ({user[1]})")
    else:
        print("\nUsers table does not exist!")
    
    # Check activity logs table
    if any(table[0] == 'user_activity_logs' for table in tables):
        print("\nUser activity logs table schema:")
        c.execute("PRAGMA table_info(user_activity_logs)")
        columns = c.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_users_db()
