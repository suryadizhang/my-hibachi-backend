#!/usr/bin/env python3
"""
Frontend-Backend sync test using browser automation approach
"""
import requests
import json
from datetime import datetime, timedelta

def test_frontend_backend_sync():
    print("🔄 Testing Frontend-Backend Sync")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    test_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
    
    print(f"📅 Test Date: {test_date}")
    
    # Step 1: Check initial availability
    print("\n1️⃣ Checking initial availability...")
    response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
    if response.status_code == 200:
        initial_availability = response.json()
        print(f"   📊 Initial slots: {json.dumps(initial_availability, indent=2)}")
        
        # Find available slot
        available_slots = [slot for slot, info in initial_availability.items() 
                          if info.get("status") == "available"]
        
        if not available_slots:
            print("   ⚠️ No available slots found")
            return False
            
        test_slot = available_slots[0]
        print(f"   🎯 Using slot: {test_slot}")
    else:
        print(f"   ❌ Failed to check availability: {response.status_code}")
        return False
    
    # Step 2: Simulate frontend booking request (exact payload format)
    print(f"\n2️⃣ Simulating frontend booking...")
    frontend_payload = {
        "name": "Frontend Test User",
        "phone": "1234567890",
        "email": "frontend@test.com", 
        "address": "123 Frontend St",
        "city": "Frontend City",
        "zipcode": "12345",
        "date": test_date,
        "time_slot": test_slot,
        "contact_preference": "email"
    }
    
    print(f"   📝 Payload: {json.dumps(frontend_payload, indent=2)}")
    
    response = requests.post(
        f"{base_url}/api/booking/book",
        json=frontend_payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Frontend Test)"
        }
    )
    
    print(f"   📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Booking successful!")
        result = response.json()
        print(f"   📄 Response: {result}")
    elif response.status_code == 422:
        print("   ❌ Validation error:")
        errors = response.json().get('detail', [])
        for error in errors:
            print(f"      {error.get('loc')}: {error.get('msg')}")
        return False
    else:
        print(f"   ❌ Booking failed: {response.text}")
        return False
    
    # Step 3: Verify slot status changed
    print(f"\n3️⃣ Verifying slot status update...")
    response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
    if response.status_code == 200:
        updated_availability = response.json()
        print(f"   📊 Updated slots: {json.dumps(updated_availability, indent=2)}")
        
        # Check if our slot status changed
        initial_status = initial_availability.get(test_slot, {}).get("status")
        updated_status = updated_availability.get(test_slot, {}).get("status")
        
        print(f"   🔄 Slot {test_slot}: {initial_status} → {updated_status}")
        
        if updated_status != initial_status:
            print("   ✅ Slot status updated correctly!")
        else:
            print("   ⚠️ Slot status unchanged")
    else:
        print(f"   ❌ Failed to verify status: {response.status_code}")
    
    # Step 4: Test error handling with invalid data
    print(f"\n4️⃣ Testing error handling...")
    invalid_payload = frontend_payload.copy()
    invalid_payload["email"] = "invalid-email"
    
    response = requests.post(
        f"{base_url}/api/booking/book",
        json=invalid_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 422:
        print("   ✅ Validation error caught correctly")
        errors = response.json().get('detail', [])
        for error in errors[:1]:  # Show first error
            print(f"      {error.get('loc')}: {error.get('msg')}")
    else:
        print(f"   ⚠️ Expected validation error, got: {response.status_code}")
    
    print(f"\n🎉 Frontend-Backend sync test completed!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    test_frontend_backend_sync()
