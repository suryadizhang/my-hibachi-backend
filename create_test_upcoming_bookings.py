#!/usr/bin/env python3
"""
Create Test Upcoming Bookings
Creates sample bookings for the next 14 days to test the upcoming events feature
"""

import sqlite3
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def create_test_bookings():
    """Create test bookings for upcoming days"""
    
    # Sample booking data
    test_bookings = []
    base_date = datetime.now(ZoneInfo("America/Los_Angeles"))
    
    # Create bookings for the next 14 days
    for i in range(14):
        booking_date = base_date + timedelta(days=i)
        date_str = booking_date.strftime("%Y-%m-%d")
        
        # Add 1-3 bookings per day
        num_bookings = min(3, (i % 3) + 1)  # 1-3 bookings per day
        
        for j in range(num_bookings):
            time_slots = ["11:00 AM", "1:00 PM", "3:00 PM", "5:00 PM", "7:00 PM"]
            time_slot = time_slots[j % len(time_slots)]
            
            booking = {
                'name': f'Test Customer {i+1}-{j+1}',
                'phone': f'555-{i:02d}{j:02d}-{(i*j+100):04d}',
                'email': f'test{i+1}{j+1}@example.com',
                'address': f'{i*100 + j*10} Test Street',
                'city': 'Los Angeles',
                'zipcode': f'900{i:02d}',
                'date': date_str,
                'time_slot': time_slot,
                'contact_preference': 'email' if j % 2 == 0 else 'phone',
                'created_at': datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
                'deposit_received': j % 2  # Some with deposit, some without
            }
            test_bookings.append(booking)
    
    # Get the correct database file for the current week
    now = datetime.now()
    year, week, _ = now.isocalendar()
    
    # Create weekly databases directory if it doesn't exist
    db_dir = "backend/weekly_databases"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create database files for current and next week
    db_files = [
        f"backend/weekly_databases/bookings_{year}-{week:02d}.db",
        f"backend/weekly_databases/bookings_{year}-{(week+1):02d}.db"
    ]
    
    total_created = 0
    
    for db_path in db_files:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create bookings table if it doesn't exist  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    zipcode TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    contact_preference TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    deposit_received INTEGER DEFAULT 0
                )
            ''')
            
            # Insert test bookings
            for booking in test_bookings:
                cursor.execute('''
                    INSERT INTO bookings 
                    (name, phone, email, address, city, zipcode, date, time_slot, 
                     contact_preference, created_at, deposit_received)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    booking['name'], booking['phone'], booking['email'],
                    booking['address'], booking['city'], booking['zipcode'],
                    booking['date'], booking['time_slot'], booking['contact_preference'],
                    booking['created_at'], booking['deposit_received']
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Created {len(test_bookings)} test bookings in {db_path}")
            total_created += len(test_bookings)
            
        except Exception as e:
            print(f"✗ Error creating bookings in {db_path}: {e}")
    
    print(f"\n✓ Total test bookings created: {total_created}")
    print("You can now test the 'Upcoming (14 days)' feature in the admin panel!")

def main():
    print("🎭 Creating Test Bookings for Upcoming Events Feature")
    print("=" * 55)
    create_test_bookings()

if __name__ == "__main__":
    main()
