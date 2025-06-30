#!/usr/bin/env python3
"""
Secure Admin Setup Script - No hardcoded passwords
"""
import sqlite3
import os
import sys
import getpass
from datetime import datetime
from zoneinfo import ZoneInfo

# Add the app directory to sys.path so we can import modules
sys.path.append(str(os.path.join(os.path.dirname(__file__), "app")))

from auth import hash_password
from database import init_user_db, get_user_db


def create_admin_account():
    """Create an admin account with user-provided credentials"""
    print("🔐 Secure Admin Account Setup")
    print("=" * 50)
    
    # Get credentials from user input
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return False
    
    password = getpass.getpass("Enter password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return False
    
    confirm_password = getpass.getpass("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return False
    
    full_name = input("Enter full name (optional): ").strip() or username.title()
    email = input("Enter email (optional): ").strip() or f"{username}@myhibachi.com"
    
    role = input("Enter role (admin/superadmin) [admin]: ").strip().lower() or "admin"
    if role not in ["admin", "superadmin"]:
        print("❌ Invalid role. Must be 'admin' or 'superadmin'")
        return False
    
    try:
        # Initialize user database
        init_user_db()
        
        conn = get_user_db()
        c = conn.cursor()
        
        # Check if username already exists
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            print(f"❌ Username '{username}' already exists")
            return False
        
        # Create the account
        current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        
        c.execute("""
            INSERT INTO users (username, password_hash, role, full_name, 
                             email, created_at, updated_at, is_active, 
                             password_reset_required, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, 
            hash_password(password), 
            role, 
            full_name,
            email, 
            current_time, 
            current_time, 
            1, 
            0,
            "secure_setup"
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ {role.title()} '{username}' created successfully")
        print(f"   Full Name: {full_name}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        print("\n⚠️ Make sure to store these credentials securely!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating account: {e}")
        return False


def main():
    """Main function"""
    if not create_admin_account():
        sys.exit(1)
    
    print("\n🎉 Account setup completed successfully!")
    print("🔒 Remember to:")
    print("   - Store credentials securely")
    print("   - Change default passwords in production")
    print("   - Use environment variables for sensitive data")


if __name__ == "__main__":
    main()
