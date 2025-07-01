#!/usr/bin/env python3
"""
Create test waitlist entries
"""
import requests
import json
from datetime import datetime, timedelta

def create_test_waitlist_entries():
    print("=== Creating Test Waitlist Entries ===\n")
    
    # Add some test waitlist entries
    waitlist_data = [
        {
            'name': 'Wait Customer 1',
            'phone': '555-1001',
            'email': 'wait1@example.com',
            'preferred_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'preferred_time': '6:00 PM'
        },
        {
            'name': 'Wait Customer 2',
            'phone': '555-1002',
            'email': 'wait2@example.com',
            'preferred_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'preferred_time': '12:00 PM'
        },
        {
            'name': 'Wait Customer 3',
            'phone': '555-1003',
            'email': 'wait3@example.com',
            'preferred_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'preferred_time': '3:00 PM'
        }
    ]

    success_count = 0
    for entry in waitlist_data:
        try:
            response = requests.post('http://localhost:8000/api/booking/waitlist', json=entry)
            if response.status_code == 200:
                print(f'✅ Added waitlist entry: {entry["name"]}')
                success_count += 1
            else:
                print(f'❌ Failed to add {entry["name"]}: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'❌ Error adding {entry["name"]}: {e}')
    
    print(f'\n=== Summary: {success_count}/{len(waitlist_data)} waitlist entries created ===')

if __name__ == "__main__":
    create_test_waitlist_entries()
