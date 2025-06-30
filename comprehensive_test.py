#!/usr/bin/env python3
"""
Comprehensive test to simulate frontend booking requests
"""
import requests
import json
from datetime import datetime, timedelta

# Test different scenarios
base_url = "http://localhost:8000"

test_cases = [
    {
        "name": "Valid booking - Clean payload",
        "payload": {
            "name": "John Doe",
            "phone": "1234567890",
            "email": "john@example.com",
            "address": "123 Main St",
            "city": "Anytown",
            "zipcode": "12345",
            "date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
            "time_slot": "3:00 PM",
            "contact_preference": "email"
        }
    },
    {
        "name": "Frontend-style payload with mixed case",
        "payload": {
            "name": "Jane Smith",
            "phone": "9876543210",
            "email": "jane@example.com",
            "address": "456 Oak Ave",
            "city": "Springfield",
            "zipcode": "54321",
            "timeSlot": "6:00 PM",  # camelCase
            "contactPreference": "phone",  # camelCase
            "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "time_slot": "6:00 PM",  # snake_case
            "contact_preference": "phone",  # snake_case
        }
    },
    {
        "name": "Missing required field",
        "payload": {
            "name": "Test User",
            "phone": "1111111111",
            "email": "test@example.com",
            "address": "789 Pine St",
            "city": "Testville",
            # Missing zipcode
            "date": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
            "time_slot": "9:00 PM",
            "contact_preference": "email"
        }
    },
    {
        "name": "Invalid email format",
        "payload": {
            "name": "Bad Email User",
            "phone": "2222222222",
            "email": "not-an-email",
            "address": "999 Test Rd",
            "city": "ErrorCity",
            "zipcode": "99999",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "time_slot": "12:00 PM",
            "contact_preference": "email"
        }
    }
]

for test_case in test_cases:
    print(f"\n{'='*50}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*50}")
    print(f"Payload: {json.dumps(test_case['payload'], indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/booking/book",
            json=test_case['payload'],
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            print(f"Response: {response.text}")
        elif response.status_code == 422:
            print("❌ VALIDATION ERROR")
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    for i, error in enumerate(error_data['detail']):
                        print(f"  Error {i+1}:")
                        print(f"    Field: {error.get('loc', 'Unknown')}")
                        print(f"    Message: {error.get('msg', 'Unknown error')}")
                        print(f"    Type: {error.get('type', 'Unknown')}")
                        print(f"    Input: {error.get('input', 'N/A')}")
            except json.JSONDecodeError:
                print(f"    Raw response: {response.text}")
        else:
            print(f"❌ ERROR - Status {response.status_code}")
            print(f"Response: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")

print(f"\n{'='*50}")
print("Test completed")
print(f"{'='*50}")
