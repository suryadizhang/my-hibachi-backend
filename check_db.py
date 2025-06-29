#!/usr/bin/env python3
import sqlite3
import os

print('=== CHECKING USERS DATABASE ===')

# Check if users.db exists
if os.path.exists('users.db'):
    print('✓ users.db exists')
    
    # Check database structure and content
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Check if users table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if c.fetchone():
            print('✓ users table exists')
            
            # Check users
            c.execute('SELECT username, role, is_active FROM users')
            users = c.fetchall()
            print(f'✓ Found {len(users)} users:')
            for user in users:
                print(f'  - {user[0]} ({user[1]}) - Active: {bool(user[2])}')
                
        else:
            print('✗ users table does not exist')
            
    except Exception as e:
        print(f'✗ Error querying users table: {e}')
    
    conn.close()
    
else:
    print('✗ users.db does not exist')
    print('Creating users.db with superadmin account...')
    
    # Create the database and table
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            full_name TEXT,
            email TEXT,
            created_at TEXT,
            updated_at TEXT,
            last_login TEXT,
            is_active INTEGER DEFAULT 1,
            password_reset_required INTEGER DEFAULT 0,
            created_by TEXT
        )
    ''')
    
    # Hash the password
    import bcrypt
    password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    from datetime import datetime
    from zoneinfo import ZoneInfo
    current_time = datetime.now(ZoneInfo('America/Los_Angeles')).isoformat()
    
    c.execute('''
        INSERT INTO users (username, password_hash, role, full_name, email, 
                          created_at, updated_at, is_active, password_reset_required, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'ady', password_hash, 'superadmin', 'Ady Admin', 'ady@myhibachi.com',
        current_time, current_time, 1, 0, 'system'
    ))
    
    conn.commit()
    conn.close()
    print('✓ Created users.db with superadmin account (ady/admin123)')

print('=== DATABASE CHECK COMPLETE ===')
