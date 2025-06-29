#!/usr/bin/env python3
"""
Show all admin accounts in the system
"""
import sqlite3
import sys
from pathlib import Path

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from database import get_user_db


def show_all_admins():
    """Display all admin accounts in the system"""
    print("👑 My Hibachi Admin Accounts")
    print("=" * 50)
    
    try:
        conn = get_user_db()
        c = conn.cursor()
        
        # Check if users table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not c.fetchone():
            print("❌ Users table does not exist!")
            print("💡 Run the migration script first: python migrate_users_db.py")
            return False
        
        # Get all users
        c.execute("""
            SELECT username, role, full_name, email, created_at, updated_at, 
                   last_login, is_active, password_reset_required, created_by
            FROM users 
            ORDER BY 
                CASE role 
                    WHEN 'superadmin' THEN 1 
                    WHEN 'admin' THEN 2 
                    ELSE 3 
                END,
                username
        """)
        
        users = c.fetchall()
        
        if not users:
            print("📭 No admin accounts found!")
            print("💡 Run the setup script: python setup_admin_accounts.py")
            return False
        
        print(f"📊 Found {len(users)} admin account(s):\n")
        
        for user in users:
            # Role icon
            role_icon = "👑" if user[1] == "superadmin" else "🔑"
            
            # Status
            status = "🟢 Active" if user[7] else "🔴 Inactive"
            
            # Password reset required
            pwd_reset = "⚠️ Password Reset Required" if user[8] else "✅ Password OK"
            
            print(f"{role_icon} {user[0]} ({user[1].upper()})")
            print(f"   📧 Email: {user[3] or 'Not set'}")
            print(f"   👤 Full Name: {user[2] or 'Not set'}")
            print(f"   📅 Created: {user[4] or 'Unknown'}")
            print(f"   🔄 Updated: {user[5] or 'Never'}")
            print(f"   🕐 Last Login: {user[6] or 'Never'}")
            print(f"   📍 Status: {status}")
            print(f"   🔑 Password: {pwd_reset}")
            print(f"   👤 Created By: {user[9] or 'Unknown'}")
            print()
        
        # Summary
        superadmin_count = sum(1 for user in users if user[1] == 'superadmin')
        admin_count = sum(1 for user in users if user[1] == 'admin')
        active_count = sum(1 for user in users if user[7])
        
        print("📈 Summary:")
        print(f"   👑 Super Admins: {superadmin_count}")
        print(f"   🔑 Regular Admins: {admin_count}")
        print(f"   🟢 Active Accounts: {active_count}")
        print(f"   🔴 Inactive Accounts: {len(users) - active_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error accessing user database: {e}")
        return False


def show_database_location():
    """Show where the user database is located"""
    db_path = Path(__file__).parent / "weekly_databases" / "users.db"
    print(f"\n📂 Database Location: {db_path}")
    print(f"📁 Database Exists: {'✅ Yes' if db_path.exists() else '❌ No'}")
    
    if db_path.exists():
        import os
        size = os.path.getsize(db_path)
        print(f"📏 Database Size: {size} bytes")


if __name__ == "__main__":
    if show_all_admins():
        show_database_location()
    else:
        print("\n💡 Troubleshooting:")
        print("   1. Run: python migrate_users_db.py")
        print("   2. Run: python setup_admin_accounts.py")
        print("   3. Run this script again")
        show_database_location()
