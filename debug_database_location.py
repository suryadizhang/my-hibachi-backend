#!/usr/bin/env python3
"""
Test admin creation through the API to see which database it uses
"""

import requests
import sqlite3
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
TEST_SUPERADMIN = {
    "username": "test_superadmin",
    "password": "TestPass123!"
}

def check_both_databases():
    """Check both users.db files to see which one has the records"""
    
    print("🔍 Checking both users.db files...")
    
    # Check root directory
    print("\n--- ROOT DIRECTORY users.db ---")
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT username, role FROM users WHERE role IN ('admin', 'superadmin') ORDER BY created_at DESC")
        users = c.fetchall()
        print(f"Users found: {len(users)}")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
    
    # Check weekly_databases directory
    print("\n--- WEEKLY_DATABASES/users.db ---")
    try:
        conn = sqlite3.connect("weekly_databases/users.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT username, role FROM users WHERE role IN ('admin', 'superadmin') ORDER BY created_at DESC")
        users = c.fetchall()
        print(f"Users found: {len(users)}")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

def create_admin_via_api():
    """Create an admin via the API to see where it gets stored"""
    
    print("\n🔐 Creating admin via API...")
    
    # Login as superadmin
    login_response = requests.post(
        f"{BASE_URL}/api/booking/admin/login",
        json=TEST_SUPERADMIN,
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Superadmin login failed: {login_response.status_code}")
        return None
        
    token = login_response.json().get("access_token")
    
    # Create a new admin
    test_username = f"api_created_{int(datetime.now().timestamp())}"
    test_password = "ApiCreated123!"
    
    create_response = requests.post(
        f"{BASE_URL}/api/booking/superadmin/create_admin",
        data={"username": test_username, "password": test_password},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    print(f"Creation response: {create_response.status_code}")
    if create_response.status_code == 200:
        print(f"✅ Created admin: {test_username}")
        return test_username, test_password
    else:
        print(f"❌ Creation failed: {create_response.text}")
        return None, None

if __name__ == "__main__":
    print("🔍 Database Location Investigation")
    print("=" * 50)
    
    # Check both databases first
    check_both_databases()
    
    # Create an admin via API
    username, password = create_admin_via_api()
    
    if username:
        print(f"\n🔍 Checking databases after API creation...")
        check_both_databases()
        
        print(f"\n🔐 Testing login for API-created admin: {username}")
        test_response = requests.post(
            f"{BASE_URL}/api/booking/admin/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        print(f"Login test: {test_response.status_code}")
        if test_response.status_code == 200:
            print("✅ API-created admin can login!")
        else:
            print(f"❌ API-created admin cannot login: {test_response.text}")
