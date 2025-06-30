#!/usr/bin/env python3
"""
Quick booking test with available slot
"""
import requests
import json
from datetime import datetime, timedelta

base_url = "http://localhost:8000"

# Test with available slot
test_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
print(f"Testing booking for date: {test_date}")

# First check what slots are available
response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
if response.status_code == 200:
    availability = response.json()
    print(f"Current availability: {json.dumps(availability, indent=2)}")
    
    # Find an available slot
    available_slot = None
    for slot, info in availability.items():
        if info.get("status") == "available":
            available_slot = slot
            break
    
    if available_slot:
        print(f"Found available slot: {available_slot}")
        
        # Try booking it
        booking_payload = {
            "name": "Quick Test User",
            "phone": "9876543210",
            "email": "quicktest@example.com",
            "address": "456 Test Ave",
            "city": "Test City",
            "zipcode": "54321",
            "date": test_date,
            "time_slot": available_slot,
            "contact_preference": "email"
        }
        
        print(f"Attempting to book {available_slot}...")
        response = requests.post(
            f"{base_url}/api/booking/book",
            json=booking_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Booking result: {response.status_code}")
        if response.status_code == 200:
            print("✅ Booking successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Booking failed: {response.text}")
            
        # Check availability after booking
        print("\nChecking availability after booking...")
        response = requests.get(f"{base_url}/api/booking/availability?date={test_date}")
        if response.status_code == 200:
            new_availability = response.json()
            print(f"Updated availability: {json.dumps(new_availability, indent=2)}")
    else:
        print("No available slots found for testing")
else:
    print(f"Failed to check availability: {response.status_code}")
