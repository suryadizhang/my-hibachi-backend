#!/usr/bin/env python3
"""
Migrate users database to the latest schema
"""
import sqlite3
import sys
from pathlib import Path

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from database import get_user_db


def migrate_users_db():
    """Migrate the users database to the latest schema"""
    print("🔄 Migrating users database to latest schema...")
    
    conn = get_user_db()
    c = conn.cursor()
    
    # Check current schema
    c.execute("PRAGMA table_info(users)")
    existing_columns = [col[1] for col in c.fetchall()]
    print(f"Current columns: {existing_columns}")
    
    # Add missing columns to users table
    new_columns = {
        'full_name': 'TEXT',
        'email': 'TEXT',
        'created_at': 'TEXT DEFAULT (datetime(\'now\'))',
        'updated_at': 'TEXT DEFAULT (datetime(\'now\'))',
        'last_login': 'TEXT',
        'is_active': 'INTEGER DEFAULT 1',
        'password_reset_required': 'INTEGER DEFAULT 0',
        'created_by': 'TEXT'
    }
    
    for column_name, column_def in new_columns.items():
        if column_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Could not add column {column_name}: {e}")
    
    # Update existing users with default values
    c.execute("""
        UPDATE users 
        SET full_name = CASE 
            WHEN username = 'admin' THEN 'System Administrator'
            WHEN username = 'testadmin' THEN 'Test Administrator'
            ELSE username
        END,
        email = CASE 
            WHEN username = 'admin' THEN 'admin@myhibachichef.com'
            WHEN username = 'testadmin' THEN 'test@myhibachichef.com'
            ELSE username || '@myhibachichef.com'
        END,
        is_active = 1,
        password_reset_required = 0,
        created_by = 'migration'
        WHERE full_name IS NULL OR email IS NULL
    """)
    
    # Check if we need to create new activity logs table
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity_logs_new'")
    if not c.fetchone():
        # Create new activity logs table with correct schema
        c.execute("""
            CREATE TABLE user_activity_logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                target_user TEXT,
                details TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Migrate existing activity logs if any
        c.execute("SELECT COUNT(*) FROM user_activity_logs")
        old_logs_count = c.fetchone()[0]
        
        if old_logs_count > 0:
            # Try to migrate old logs to new format
            c.execute("""
                INSERT INTO user_activity_logs_new (user_id, action, target_user, details, timestamp, ip_address)
                SELECT 
                    u.id,
                    ual.action_type,
                    ual.target_username,
                    ual.description,
                    ual.timestamp,
                    ual.ip_address
                FROM user_activity_logs ual
                LEFT JOIN users u ON ual.admin_username = u.username
            """)
            print(f"✅ Migrated {old_logs_count} activity log entries")
        
        # Drop old table and rename new one
        c.execute("DROP TABLE user_activity_logs")
        c.execute("ALTER TABLE user_activity_logs_new RENAME TO user_activity_logs")
        print("✅ Updated activity logs table schema")
    
    conn.commit()
    conn.close()
    
    print("✅ Database migration completed!")
    return True


if __name__ == "__main__":
    print("🚀 My Hibachi Database Migration")
    print("=" * 50)
    
    if migrate_users_db():
        print("\n🎉 Migration completed successfully!")
        print("Ready to run admin account setup...")
    else:
        print("\n❌ Migration failed!")
