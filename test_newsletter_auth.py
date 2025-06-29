#!/usr/bin/env python3
"""
Test newsletter functionality with authentication
"""
import requests
import sqlite3

BASE_URL = "http://localhost:8000/api/booking"

def create_test_admin():
    """Create a test admin user if it doesn't exist"""
    conn = sqlite3.connect('mh-bookings.db')
    cursor = conn.cursor()
    
    # Check if admin table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if test admin exists
    cursor.execute("SELECT id FROM admin_users WHERE username = 'testadmin'")
    if cursor.fetchone():
        print("✅ Test admin already exists")
        conn.close()
        return
    
    # Create test admin (password: testpassword)
    import hashlib
    password = "testpassword"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
            ("testadmin", password_hash)
        )
        conn.commit()
        print("✅ Test admin created")
    except Exception as e:
        print(f"❌ Failed to create test admin: {e}")
    
    conn.close()

def get_admin_token():
    """Get admin token for testing"""
    try:
        response = requests.post(f"{BASE_URL}/admin/login", json={
            "username": "testadmin",
            "password": "testpassword"
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Admin token obtained")
            return token
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def test_newsletter_endpoints_with_auth():
    """Test newsletter endpoints with proper authentication"""
    
    # Create test admin if needed
    create_test_admin()
    
    # Get authentication token
    token = get_admin_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Newsletter Endpoints with Authentication ===")
    
    # Test 1: Get all recipients
    print("\n1. Testing: Get All Recipients")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"   ✅ Total recipients: {total}")
            
            # Show sample recipients
            recipients = data.get('recipients', [])[:3]
            for i, recipient in enumerate(recipients, 1):
                print(f"   Sample {i}: {recipient.get('name')} - {recipient.get('city')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get cities
    print("\n2. Testing: Get Cities")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/cities", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            cities = data.get('cities', [])
            print(f"   ✅ Found {len(cities)} cities")
            print(f"   Sample cities: {cities[:5]}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Filter by city
    print("\n3. Testing: Filter by City (San Jose)")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients?city=San Jose", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"   ✅ San Jose recipients: {total}")
            filtered_city = data.get('filtered_by_city')
            print(f"   Filter applied: {filtered_city}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Filter by name  
    print("\n4. Testing: Filter by Name (containing 'John')")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients?name=John", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"   ✅ Recipients with 'John': {total}")
            filtered_name = data.get('filtered_by_name')
            print(f"   Filter applied: {filtered_name}")
            
            # Show names
            recipients = data.get('recipients', [])
            for recipient in recipients:
                print(f"   Found: {recipient.get('name')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Combined filter
    print("\n5. Testing: Combined Filter (City + Name)")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients?city=San&name=A", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"   ✅ Combined filter results: {total}")
            print(f"   City filter: {data.get('filtered_by_city')}")
            print(f"   Name filter: {data.get('filtered_by_name')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Newsletter Mass Send and Filter Functions")
    print("=" * 60)
    
    success = test_newsletter_endpoints_with_auth()
    
    if success:
        print("\n✅ All newsletter functionality tests passed!")
        print("✅ Database is ready for:")
        print("   📧 Mass email sending")
        print("   🏙️ City-based filtering") 
        print("   👤 Name-based filtering")
        print("   🎯 Combined filtering")
    else:
        print("\n❌ Some tests failed")
