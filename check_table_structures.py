#!/usr/bin/env python3
"""
Check database table structures
"""

import sqlite3

def check_table_structure():
    """Check the structure of tables in both databases"""
    
    # Check users.db
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        
        print("--- USERS.DB TABLE STRUCTURES ---")
        
        # Get all tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            c.execute(f"PRAGMA table_info({table_name})")
            columns = c.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
        conn.close()
    except Exception as e:
        print(f"Error checking users.db: {e}")
    
    # Check mh-bookings.db
    try:
        conn = sqlite3.connect("mh-bookings.db")
        c = conn.cursor()
        
        print("\n--- MH-BOOKINGS.DB TABLE STRUCTURES ---")
        
        # Get all tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            c.execute(f"PRAGMA table_info({table_name})")
            columns = c.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
        conn.close()
    except Exception as e:
        print(f"Error checking mh-bookings.db: {e}")

if __name__ == "__main__":
    check_table_structure()
