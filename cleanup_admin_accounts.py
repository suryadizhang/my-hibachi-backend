#!/usr/bin/env python3
"""
Clean up admin accounts - keep only production accounts (ady, karen, yohan)
"""
import sys
from pathlib import Path

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from database import get_user_db


def cleanup_admin_accounts():
    """Remove unnecessary admin accounts, keep only production accounts"""
    print("🧹 Cleaning up admin accounts...")
    print("Keeping only: ady, karen, yohan")
    
    # Production accounts to keep
    keep_accounts = ['ady', 'karen', 'yohan']
    
    conn = get_user_db()
    c = conn.cursor()
    
    # Get all current users
    c.execute("SELECT username, role FROM users ORDER BY username")
    all_users = c.fetchall()
    
    print(f"\n📋 Current accounts ({len(all_users)}):")
    for user in all_users:
        keep_status = "✅ KEEP" if user[0] in keep_accounts else "❌ DELETE"
        role_icon = "👑" if user[1] == "superadmin" else "🔑"
        print(f"   {role_icon} {user[0]} ({user[1]}) - {keep_status}")
    
    # Find accounts to delete
    accounts_to_delete = [user[0] for user in all_users if user[0] not in keep_accounts]
    
    if not accounts_to_delete:
        print("\n✅ No accounts need to be deleted!")
        conn.close()
        return True
    
    print(f"\n🗑️ Accounts to delete: {', '.join(accounts_to_delete)}")
    
    # Delete unwanted accounts
    deleted_count = 0
    for username in accounts_to_delete:
        try:
            c.execute("DELETE FROM users WHERE username = ?", (username,))
            print(f"✅ Deleted: {username}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting {username}: {e}")
    
    # Also clean up any related activity logs for deleted users
    try:
        c.execute("DELETE FROM user_activity_logs WHERE target_user NOT IN (?, ?, ?)", 
                 ('ady', 'karen', 'yohan'))
        logs_deleted = c.rowcount
        if logs_deleted > 0:
            print(f"🧹 Cleaned up {logs_deleted} old activity log entries")
    except Exception as e:
        print(f"⚠️ Could not clean activity logs: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   🗑️ Deleted: {deleted_count} accounts")
    print(f"   ✅ Remaining: {len(all_users) - deleted_count} accounts")
    
    return True


def verify_final_accounts():
    """Verify that only the correct accounts remain"""
    print("\n🔍 Verifying final admin accounts...")
    
    conn = get_user_db()
    c = conn.cursor()
    
    c.execute("SELECT username, role, full_name, email FROM users ORDER BY role DESC, username")
    users = c.fetchall()
    
    print(f"\n✅ Final admin accounts ({len(users)}):")
    for user in users:
        role_icon = "👑" if user[1] == "superadmin" else "🔑"
        print(f"   {role_icon} {user[0]} ({user[1].upper()})")
        print(f"      👤 {user[2]}")
        print(f"      📧 {user[3]}")
        print()
    
    # Verify we have exactly the right accounts
    expected_accounts = ['ady', 'karen', 'yohan']
    actual_accounts = [user[0] for user in users]
    
    if set(actual_accounts) == set(expected_accounts):
        print("🎉 Perfect! Only production accounts remain.")
        
        # Verify roles are correct
        ady_role = next((user[1] for user in users if user[0] == 'ady'), None)
        karen_role = next((user[1] for user in users if user[0] == 'karen'), None)
        yohan_role = next((user[1] for user in users if user[0] == 'yohan'), None)
        
        if ady_role == 'superadmin' and karen_role == 'admin' and yohan_role == 'admin':
            print("✅ All roles are correctly assigned!")
            print("\n📝 Production Summary:")
            print("   👑 Super Admin: ady (13Agustus!)")
            print("   🔑 Admin: karen (myhibachicustomers!)")
            print("   🔑 Admin: yohan (gedeinbiji)")
            print("\n🚀 System ready for production deployment!")
        else:
            print("⚠️ Warning: Some roles may be incorrect")
    else:
        print("⚠️ Warning: Account list doesn't match expected production accounts")
        print(f"Expected: {expected_accounts}")
        print(f"Actual: {actual_accounts}")
    
    conn.close()
    return True


if __name__ == "__main__":
    print("🚀 My Hibachi Admin Account Cleanup")
    print("=" * 50)
    
    if cleanup_admin_accounts():
        verify_final_accounts()
    else:
        print("\n❌ Cleanup failed!")
