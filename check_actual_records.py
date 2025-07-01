#!/usr/bin/env python3
"""
Check actual database contents after admin creation
"""

import sqlite3

def check_actual_records():
    """Check what's actually in the databases"""
    
    # Check users.db
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        print("--- USERS.DB RECORDS ---")
        c.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 10")
        users = c.fetchall()
        print(f"Recent users: {len(users)}")
        for user in users:
            print(f"  - {user['username']} (role: {user['role']}, active: {user['is_active']})")
            
        # Check admins table
        c.execute("SELECT * FROM admins ORDER BY created_at DESC LIMIT 10")
        admins = c.fetchall()
        print(f"Admins in users.db: {len(admins)}")
        for admin in admins:
            print(f"  - {admin['username']} (type: {admin['user_type']})")
            
        conn.close()
    except Exception as e:
        print(f"Error checking users.db: {e}")
    
    # Check mh-bookings.db
    try:
        conn = sqlite3.connect("mh-bookings.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        print("\n--- MH-BOOKINGS.DB RECORDS ---")
        c.execute("SELECT * FROM admins ORDER BY created_at DESC LIMIT 10")
        admins = c.fetchall()
        print(f"Admins in mh-bookings.db: {len(admins)}")
        for admin in admins:
            print(f"  - {admin['username']} (type: {admin['user_type']}, active: {admin.get('is_active', 'N/A')})")
            
        conn.close()
    except Exception as e:
        print(f"Error checking mh-bookings.db: {e}")

if __name__ == "__main__":
    check_actual_records()
