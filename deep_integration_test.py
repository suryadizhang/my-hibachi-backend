#!/usr/bin/env python3
"""
Deep integration test for the booking system - tests the full flow
"""
import requests
import json
from datetime import datetime, timedelta
import time

base_url = "http://localhost:8000"

def test_booking_integration():
    print("🚀 Starting Deep Booking Integration Test")
    print("=" * 60)
    
    # Test 1: Check availability endpoint
    print("\n📅 Test 1: Check Availability Endpoint")
    test_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
        print(f"✅ Availability API: {response.status_code}")
        if response.status_code == 200:
            availability = response.json()
            print(f"   Slots available: {json.dumps(availability, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Availability API failed: {e}")
        return False
    
    # Test 2: Full booking flow with valid data
    print(f"\n📝 Test 2: Complete Booking Flow")
    booking_payload = {
        "name": "Integration Test User",
        "phone": "1234567890",
        "email": "integration@test.com",
        "address": "123 Integration St",
        "city": "Test City",
        "zipcode": "12345",
        "date": test_date,
        "time_slot": "12:00 PM",
        "contact_preference": "email"
    }
    
    print(f"   📋 Booking data: {json.dumps(booking_payload, indent=4)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/booking/book",
            json=booking_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Booking successful!")
            print(f"   📄 Response: {response.json()}")
        elif response.status_code == 422:
            print("   ❌ Validation error:")
            error_data = response.json()
            for error in error_data.get('detail', []):
                print(f"      Field: {error.get('loc', 'Unknown')}")
                print(f"      Error: {error.get('msg', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Booking failed: {e}")
        return False
    
    # Test 3: Check availability after booking (should show occupied slot)
    print(f"\n🔄 Test 3: Verify Slot Status After Booking")
    try:
        response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
        if response.status_code == 200:
            new_availability = response.json()
            print(f"   📊 Updated availability: {json.dumps(new_availability, indent=2)}")
            
            # Check if 12:00 PM slot status changed
            if new_availability.get("12:00 PM", {}).get("status") in ["waiting", "booked"]:
                print("   ✅ Slot status updated correctly")
            else:
                print("   ⚠️ Slot status may not have updated as expected")
        else:
            print(f"   ❌ Failed to check updated availability: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Availability check failed: {e}")
    
    # Test 4: Try to book the same slot again (should fail if slot limit reached)
    print(f"\n🚫 Test 4: Double Booking Prevention")
    duplicate_payload = booking_payload.copy()
    duplicate_payload["email"] = "duplicate@test.com"
    duplicate_payload["name"] = "Duplicate Test User"
    
    try:
        response = requests.post(
            f"{base_url}/api/booking/book",
            json=duplicate_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 400:
            print("   ✅ Double booking prevented correctly")
            print(f"   📄 Response: {response.json()}")
        elif response.status_code == 200:
            print("   ⚠️ Second booking allowed (slot has capacity for 2)")
            print(f"   📄 Response: {response.json()}")
        else:
            print(f"   ❓ Unexpected response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Duplicate booking test failed: {e}")
    
    # Test 5: Invalid data validation
    print(f"\n❌ Test 5: Validation Testing")
    invalid_payloads = [
        {
            "name": "Invalid Email Test",
            "payload": {**booking_payload, "email": "not-an-email", "date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")},
            "expected_error": "email validation"
        },
        {
            "name": "Missing Required Field",
            "payload": {k: v for k, v in booking_payload.items() if k != "zipcode"},
            "expected_error": "missing field"
        },
        {
            "name": "Past Date Booking",
            "payload": {**booking_payload, "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")},
            "expected_error": "past date" # This might not be validated at API level
        }
    ]
    
    for test_case in invalid_payloads:
        print(f"\n   🧪 {test_case['name']}:")
        try:
            response = requests.post(
                f"{base_url}/api/booking/book",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 422:
                print(f"   ✅ Validation caught correctly")
                errors = response.json().get('detail', [])
                for error in errors[:2]:  # Show first 2 errors
                    print(f"      {error.get('loc', 'Unknown')}: {error.get('msg', 'Unknown')}")
            elif response.status_code == 200:
                print(f"   ⚠️ Validation missed - request succeeded unexpectedly")
            else:
                print(f"   ❓ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n🏁 Deep Integration Test Complete")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_booking_integration()
