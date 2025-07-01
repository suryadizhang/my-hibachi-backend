#!/usr/bin/env python3
"""
Debug password hashing and authentication
"""

import sqlite3
import bcrypt
from datetime import datetime

def check_password_hash():
    """Check the password hash in the database vs what we expect"""
    
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get the most recent admin
    c.execute("SELECT * FROM users WHERE role='admin' ORDER BY created_at DESC LIMIT 1")
    user = c.fetchone()
    
    if not user:
        print("❌ No admin found")
        return
        
    print(f"🔍 Checking admin: {user['username']}")
    print(f"Role: {user['role']}")
    print(f"Active: {user['is_active']}")
    print(f"Hash in DB: {user['password_hash'][:50]}...")
    
    # Test different passwords
    test_passwords = ["ManualTest123!", "ApiTest123!", "DebugPass123!"]
    
    for password in test_passwords:
        try:
            # Check if the password matches
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                print(f"✅ Password '{password}' matches!")
                return password
            else:
                print(f"❌ Password '{password}' does not match")
        except Exception as e:
            print(f"❌ Error checking password '{password}': {e}")
    
    return None

def create_test_admin_with_known_password():
    """Create a test admin with a known password for debugging"""
    
    username = f"debug_test_{int(datetime.now().timestamp())}"
    password = "KnownPass123!"
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        current_time = datetime.now().isoformat()
        
        c.execute("""
            INSERT INTO users (username, password_hash, role, full_name, 
                             email, created_at, updated_at, is_active, 
                             password_reset_required, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, password_hash, "admin", username.title(),
            f"{username}@myhibachi.com", current_time, current_time, 1, 0,
            "debug_script"
        ))
        
        conn.commit()
        print(f"✅ Created test admin: {username} with password: {password}")
        
        # Verify it was created
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        created_user = c.fetchone()
        
        if created_user:
            print(f"✅ Verified creation - Role: {created_user['role']}, Active: {created_user['is_active']}")
            
            # Test the password immediately
            if bcrypt.checkpw(password.encode('utf-8'), created_user['password_hash'].encode('utf-8')):
                print("✅ Password verification works locally")
                return username, password
            else:
                print("❌ Password verification failed locally")
        else:
            print("❌ User not found after creation")
            
    except Exception as e:
        print(f"❌ Error creating test admin: {e}")
        
    finally:
        conn.close()
    
    return None, None

if __name__ == "__main__":
    print("🔍 Checking existing admin password hash...")
    check_password_hash()
    
    print("\n🧪 Creating test admin with known password...")
    test_username, test_password = create_test_admin_with_known_password()
    
    if test_username and test_password:
        print(f"\n✅ Test admin created: {test_username} / {test_password}")
        print("You can now test authentication with this admin")
