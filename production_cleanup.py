#!/usr/bin/env python3
"""
Production Cleanup Script
Removes test accounts and prepares system for production deployment
"""

import sqlite3
import os
import sys


def remove_test_accounts():
    """Remove test admin accounts before production"""
    
    test_usernames = [
        "test_superadmin",
        "test_admin",
        "admin_test",
        "demo_admin"
    ]
    
    databases = [
        "mh-bookings.db",
        "users.db"
    ]
    
    print("🧹 Production Cleanup - Removing Test Accounts")
    print("=" * 50)
    
    total_removed = 0
    
    for db_path in databases:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for username in test_usernames:
                    # Check and remove from admins table
                    cursor.execute(
                        "SELECT COUNT(*) FROM admins WHERE username = ?",
                        (username,)
                    )
                    if cursor.fetchone()[0] > 0:
                        cursor.execute(
                            "DELETE FROM admins WHERE username = ?",
                            (username,)
                        )
                        print(f"✓ Removed test admin '{username}' from {db_path}")
                        total_removed += 1
                    
                    # Check and remove from users table (if exists)
                    try:
                        cursor.execute(
                            "SELECT COUNT(*) FROM users WHERE username = ?",
                            (username,)
                        )
                        if cursor.fetchone()[0] > 0:
                            cursor.execute(
                                "DELETE FROM users WHERE username = ?",
                                (username,)
                            )
                            print(f"✓ Removed test user '{username}' from {db_path}")
                            total_removed += 1
                    except sqlite3.OperationalError:
                        # Users table doesn't exist, skip
                        pass
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"✗ Error processing {db_path}: {e}")
                return False
        else:
            print(f"! Database {db_path} not found, skipping")
    
    print(f"\n✓ Production cleanup complete!")
    print(f"Removed {total_removed} test accounts")
    
    if total_removed == 0:
        print("No test accounts found - system is already clean")
    
    return True


def main():
    """Main cleanup function"""
    print("This script will remove all test admin accounts from the system.")
    print("This should be run before production deployment.")
    
    response = input("\nContinue with cleanup? (y/N): ").lower().strip()
    
    if response != 'y':
        print("Cleanup cancelled.")
        return 0
    
    if remove_test_accounts():
        print("\n🚀 System is now ready for production deployment!")
        print("\nNext steps:")
        print("1. Create production admin accounts using secure_admin_setup.py")
        print("2. Configure production environment variables")
        print("3. Deploy with HTTPS enabled")
        return 0
    else:
        print("\n❌ Cleanup failed. Please check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
