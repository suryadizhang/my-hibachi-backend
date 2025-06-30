#!/usr/bin/env python3
"""
Test script to directly test the booking API endpoint
"""
import requests
import json
from datetime import datetime, timedelta

# Test data
base_url = "http://localhost:8000"

# Test payload that matches what frontend should send
test_payload = {
    "name": "Test User",
    "phone": "1234567890", 
    "email": "test@example.com",
    "address": "123 Test St",
    "city": "Testville",
    "zipcode": "12345",
    "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),  # 3 days from now
    "time_slot": "12:00 PM",
    "contact_preference": "email"
}

print("Testing booking endpoint...")
print(f"Payload: {json.dumps(test_payload, indent=2)}")

try:
    response = requests.post(
        f"{base_url}/api/booking/book",
        json=test_payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 422:
        print("\n=== VALIDATION ERROR DETAILS ===")
        error_data = response.json()
        if 'detail' in error_data:
            for error in error_data['detail']:
                print(f"Field: {error.get('loc', 'Unknown')}")
                print(f"Message: {error.get('msg', 'Unknown error')}")
                print(f"Type: {error.get('type', 'Unknown')}")
                print("---")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
