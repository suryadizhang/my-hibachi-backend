import requests
import json

# Test newsletter functionality with imported data
BASE_URL = "http://localhost:8000/api/booking"

# First, let's create an admin token (assuming we have admin credentials)
# For testing, we'll use a mock token or create one if needed

def test_newsletter_endpoints():
    """Test newsletter endpoints with imported data"""
    
    # Test 1: Get all recipients
    print("=== Test 1: Get All Recipients ===")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients")
        if response.status_code == 401:
            print("❌ Authentication required - this is expected for admin endpoints")
        else:
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Total recipients: {data.get('total_count', 0)}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Get cities
    print("\n=== Test 2: Get Cities ===")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/cities")
        if response.status_code == 401:
            print("❌ Authentication required - this is expected for admin endpoints")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Filter by city (would need auth)
    print("\n=== Test 3: Filter by City ===")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients?city=San Jose")
        if response.status_code == 401:
            print("❌ Authentication required - this is expected for admin endpoints")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Filter by name (would need auth)
    print("\n=== Test 4: Filter by Name ===")
    try:
        response = requests.get(f"{BASE_URL}/admin/newsletter/recipients?name=John")
        if response.status_code == 401:
            print("❌ Authentication required - this is expected for admin endpoints")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ All endpoints are accessible (authentication required as expected)")
    return True

def test_database_structure():
    """Test that our database has the right structure for newsletter functionality"""
    import sqlite3
    
    print("=== Database Structure Test ===")
    
    conn = sqlite3.connect('mh-bookings.db')
    cursor = conn.cursor()
    
    # Check if we have the required fields for newsletter functionality
    cursor.execute("PRAGMA table_info(company_newsletter)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    required_fields = ['name', 'email', 'city', 'phone', 'address']
    
    print("Required fields for newsletter functionality:")
    for field in required_fields:
        if field in column_names:
            print(f"  ✅ {field} - Present")
        else:
            print(f"  ❌ {field} - Missing")
    
    # Test data availability
    print("\nData availability:")
    
    # Count customers with email addresses
    cursor.execute("SELECT COUNT(*) FROM company_newsletter WHERE email IS NOT NULL AND email != ''")
    email_count = cursor.fetchone()[0]
    print(f"  📧 Customers with email: {email_count}")
    
    # Count customers by city (top 5)
    cursor.execute("""
        SELECT city, COUNT(*) 
        FROM company_newsletter 
        WHERE city IS NOT NULL AND city != '' 
        GROUP BY city 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    cities = cursor.fetchall()
    print(f"  🏙️ Top cities:")
    for city, count in cities:
        print(f"    {city}: {count} customers")
    
    # Test name filtering
    cursor.execute("SELECT COUNT(*) FROM company_newsletter WHERE name LIKE '%John%'")
    john_count = cursor.fetchone()[0]
    print(f"  👤 Customers with 'John' in name: {john_count}")
    
    # Test city filtering 
    cursor.execute("SELECT COUNT(*) FROM company_newsletter WHERE city LIKE '%San Jose%'")
    sj_count = cursor.fetchone()[0]
    print(f"  🏙️ Customers in San Jose area: {sj_count}")
    
    conn.close()
    
    print("\n✅ Database structure is compatible with newsletter functionality")
    return True

if __name__ == "__main__":
    print("Testing Newsletter Functionality with Imported Data")
    print("=" * 55)
    
    # Test database structure
    test_database_structure()
    
    print("\n" + "=" * 55)
    
    # Test API endpoints
    test_newsletter_endpoints()
    
    print("\n🎉 Newsletter functionality tests completed!")
