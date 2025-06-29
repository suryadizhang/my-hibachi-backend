#!/usr/bin/env python3
"""
Show all admin accounts in the system (simple version)
"""
import sys
from pathlib import Path

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from database import get_user_db


def show_all_admins_simple():
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
            return False
        
        # Get table info to see what columns exist
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        print(f"🔍 Available columns: {', '.join(columns)}")
        
        # Get all users with available columns
        c.execute("SELECT username, role FROM users ORDER BY role DESC, username")
        users = c.fetchall()
        
        if not users:
            print("📭 No admin accounts found!")
            return False
        
        print(f"\n📊 Found {len(users)} admin account(s):\n")
        
        for user in users:
            # Role icon
            role_icon = "👑" if user[1] == "superadmin" else "🔑"
            
            print(f"{role_icon} {user[0]} ({user[1].upper()})")
            
            # Get additional info if columns exist
            if 'full_name' in columns:
                c.execute("SELECT full_name FROM users WHERE username = ?", (user[0],))
                full_name = c.fetchone()
                if full_name and full_name[0]:
                    print(f"   👤 Full Name: {full_name[0]}")
            
            if 'email' in columns:
                c.execute("SELECT email FROM users WHERE username = ?", (user[0],))
                email = c.fetchone()
                if email and email[0]:
                    print(f"   📧 Email: {email[0]}")
            
            if 'is_active' in columns:
                c.execute("SELECT is_active FROM users WHERE username = ?", (user[0],))
                is_active = c.fetchone()
                if is_active is not None:
                    status = "🟢 Active" if is_active[0] else "🔴 Inactive"
                    print(f"   📍 Status: {status}")
            
            if 'password_reset_required' in columns:
                c.execute("SELECT password_reset_required FROM users WHERE username = ?", (user[0],))
                pwd_reset = c.fetchone()
                if pwd_reset is not None:
                    reset_status = "⚠️ Password Reset Required" if pwd_reset[0] else "✅ Password OK"
                    print(f"   🔑 Password: {reset_status}")
            
            print()
        
        # Summary
        superadmin_count = sum(1 for user in users if user[1] == 'superadmin')
        admin_count = sum(1 for user in users if user[1] == 'admin')
        
        print("📈 Summary:")
        print(f"   👑 Super Admins: {superadmin_count}")
        print(f"   🔑 Regular Admins: {admin_count}")
        print(f"   📊 Total Accounts: {len(users)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error accessing user database: {e}")
        return False


if __name__ == "__main__":
    show_all_admins_simple()
