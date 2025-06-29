#!/usr/bin/env python3
"""
Setup production admin accounts (compatible with current schema)
"""
import sys
from pathlib import Path

# Add the app directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent / "app"))

from auth import hash_password
from database import get_user_db


def setup_production_accounts():
    """Create production admin accounts"""
    print("🔧 Setting up production admin accounts...")
    
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
    
    # Check what columns exist
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    print(f"Available columns: {', '.join(columns)}")
    
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
                update_parts = ["password_hash = ?", "role = ?"]
                params = [hash_password(account["password"]), account["role"]]
                
                if 'full_name' in columns:
                    update_parts.append("full_name = ?")
                    params.append(account["full_name"])
                
                if 'email' in columns:
                    update_parts.append("email = ?")
                    params.append(account["email"])
                
                if 'is_active' in columns:
                    update_parts.append("is_active = 1")
                
                if 'password_reset_required' in columns:
                    update_parts.append("password_reset_required = 0")
                
                params.append(account["username"])
                
                query = f"UPDATE users SET {', '.join(update_parts)} WHERE username = ?"
                c.execute(query, params)
                
                print(f"✅ Updated {account['role']}: {account['username']}")
                updated_count += 1
            else:
                # Create new user
                insert_columns = ["username", "password_hash", "role"]
                insert_values = ["?", "?", "?"]
                params = [account["username"], hash_password(account["password"]), account["role"]]
                
                if 'full_name' in columns:
                    insert_columns.append("full_name")
                    insert_values.append("?")
                    params.append(account["full_name"])
                
                if 'email' in columns:
                    insert_columns.append("email")
                    insert_values.append("?")
                    params.append(account["email"])
                
                if 'is_active' in columns:
                    insert_columns.append("is_active")
                    insert_values.append("1")
                
                if 'created_by' in columns:
                    insert_columns.append("created_by")
                    insert_values.append("'system'")
                
                query = f"INSERT INTO users ({', '.join(insert_columns)}) VALUES ({', '.join(insert_values)})"
                c.execute(query, params)
                
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


if __name__ == "__main__":
    print("🚀 My Hibachi Production Account Setup")
    print("=" * 50)
    
    if setup_production_accounts():
        print("\n🎉 Production accounts setup completed!")
        print("\n📝 Account Summary:")
        print("   👑 Super Admin: ady (password: 13Agustus!)")
        print("   🔑 Admin: karen (password: myhibachicustomers!)")
        print("   🔑 Admin: yohan (password: gedeinbiji)")
        print("\n🚀 System ready for production!")
    else:
        print("\n❌ Setup failed!")
