#!/usr/bin/env python3
"""
Setup default admin accounts for production deployment
Creates superadmin and admin accounts with specified credentials
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import sys

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from auth import hash_password
from database import init_user_db, get_user_db


def setup_default_accounts():
    """Create default admin accounts for production"""
    print("🔧 Setting up default admin accounts...")
    
    # Initialize user database
    init_user_db()
    
    # Account configurations
    accounts = [
        {
            "username": "ady",
            "password": "13Agustus!",
            "role": "superadmin",
            "full_name": "Ady (Super Administrator)",
            "email": "ady@myhibachichef.com"
        },
        {
            "username": "karen",
            "password": "myhibachicustomers!",
            "role": "admin",
            "full_name": "Karen (Administrator)",
            "email": "karen@myhibachichef.com"
        },
        {
            "username": "yohan",
            "password": "gedeinbiji",
            "role": "admin",
            "full_name": "Yohan (Administrator)",
            "email": "yohan@myhibachichef.com"
        }
    ]
    
    conn = get_user_db()
    c = conn.cursor()
    
    created_count = 0
    updated_count = 0
    
    for account in accounts:
        try:
            # Check if user already exists
            c.execute("SELECT id, username, role FROM users WHERE username = ?", 
                     (account["username"],))
            existing = c.fetchone()
            
            if existing:
                # Update existing user
                c.execute("""
                    UPDATE users 
                    SET password_hash = ?, role = ?, full_name = ?, email = ?, 
                        updated_at = datetime('now'), is_active = 1,
                        password_reset_required = 0
                    WHERE username = ?
                """, (
                    hash_password(account["password"]),
                    account["role"],
                    account["full_name"],
                    account["email"],
                    account["username"]
                ))
                print(f"✅ Updated {account['role']}: {account['username']}")
                updated_count += 1
            else:
                # Create new user
                c.execute("""
                    INSERT INTO users 
                    (username, password_hash, role, full_name, email, 
                     created_at, updated_at, is_active, created_by)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1, 'system')
                """, (
                    account["username"],
                    hash_password(account["password"]),
                    account["role"],
                    account["full_name"],
                    account["email"]
                ))
                print(f"✅ Created {account['role']}: {account['username']}")
                created_count += 1
                
        except Exception as e:
            print(f"❌ Error setting up {account['username']}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Setup Summary:")
    print(f"   Created: {created_count} accounts")
    print(f"   Updated: {updated_count} accounts")
    print(f"   Total: {created_count + updated_count} accounts configured")
    
    return True


def verify_accounts():
    """Verify that all accounts were created successfully"""
    print("\n🔍 Verifying admin accounts...")
    
    conn = get_user_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT username, role, full_name, email, is_active, created_at 
        FROM users 
        ORDER BY role DESC, username
    """)
    
    accounts = c.fetchall()
    
    if not accounts:
        print("❌ No accounts found!")
        return False
    
    print(f"\n📋 Found {len(accounts)} admin accounts:")
    for account in accounts:
        status = "🟢 Active" if account["is_active"] else "🔴 Inactive"
        role_icon = "👑" if account["role"] == "superadmin" else "🔑"
        print(f"   {role_icon} {account['username']} ({account['role']}) - {status}")
        print(f"      Name: {account['full_name']}")
        print(f"      Email: {account['email']}")
        print(f"      Created: {account['created_at']}")
        print()
    
    conn.close()
    return True


def test_login(username, password):
    """Test login functionality for an account"""
    from auth import verify_password
    
    conn = get_user_db()
    c = conn.cursor()
    
    c.execute("SELECT username, password_hash, role FROM users WHERE username = ?", 
             (username,))
    user = c.fetchone()
    
    if user and verify_password(password, user["password_hash"]):
        print(f"✅ Login test successful for {username} ({user['role']})")
        return True
    else:
        print(f"❌ Login test failed for {username}")
        return False


if __name__ == "__main__":
    print("🚀 My Hibachi Admin Account Setup")
    print("=" * 50)
    
    # Setup accounts
    if setup_default_accounts():
        # Verify accounts
        if verify_accounts():
            print("🧪 Testing login functionality...")
            
            # Test each account
            test_accounts = [
                ("ady", "13Agustus!"),
                ("karen", "myhibachicustomers!"),
                ("yohan", "gedeinbiji")
            ]
            
            success_count = 0
            for username, password in test_accounts:
                if test_login(username, password):
                    success_count += 1
            
            if success_count == len(test_accounts):
                print(f"\n🎉 All {len(test_accounts)} accounts setup and verified successfully!")
                print("\n📝 Account Summary:")
                print("   👑 Super Admin: ady (password: 13Agustus!)")
                print("   🔑 Admin: karen (password: myhibachicustomers!)")
                print("   🔑 Admin: yohan (password: gedeinbiji)")
                print("\n🚀 System ready for production deployment!")
            else:
                print(f"\n⚠️ {success_count}/{len(test_accounts)} login tests passed")
        else:
            print("❌ Account verification failed")
    else:
        print("❌ Account setup failed")
