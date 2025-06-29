"""
Sample Database Generator for Testing
Creates fake data for the My Hibachi booking system for testing purposes.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker
import os

fake = Faker()

def create_sample_database():
    """Create a sample database with fake data for testing."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'sample_test.db')
    
    # Remove existing sample database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    create_tables(c)
    
    # Insert fake data
    insert_fake_bookings(c)
    insert_fake_newsletter_subscribers(c)
    insert_fake_waitlist(c)
    insert_fake_activity_logs(c)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created at: {db_path}")
    return db_path

def create_tables(cursor):
    """Create all necessary tables."""
    # Bookings table
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deposit_received INTEGER DEFAULT 0
        )
    ''')
    
    # Newsletter subscribers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT NOT NULL UNIQUE,
            address TEXT,
            city TEXT,
            zipcode TEXT,
            last_activity_date TEXT,
            source TEXT
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('superadmin', 'admin')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Waitlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Activity logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            description TEXT NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    ''')

def insert_fake_bookings(cursor):
    """Insert fake booking data."""
    print("Creating fake bookings...")
    
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
              'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
    time_slots = ['11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM', 
                  '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM', '8:00 PM']
    contact_prefs = ['email', 'phone', 'text']
    
    # Generate bookings for the next 30 days
    start_date = datetime.now()
    
    for i in range(50):  # 50 fake bookings
        booking_date = start_date + timedelta(days=random.randint(0, 30))
        city = random.choice(cities)
        
        cursor.execute('''
            INSERT INTO bookings 
            (name, phone, email, address, city, zipcode, date, time_slot, 
             contact_preference, created_at, deposit_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.name(),
            fake.phone_number(),
            fake.email(),
            fake.street_address(),
            city,
            fake.zipcode(),
            booking_date.strftime('%Y-%m-%d'),
            random.choice(time_slots),
            random.choice(contact_prefs),
            fake.date_time_between(start_date='-30d', end_date='now'),
            random.choice([0, 0, 0, 1])  # 25% have deposit received
        ))

def insert_fake_newsletter_subscribers(cursor):
    """Insert fake newsletter subscriber data."""
    print("Creating fake newsletter subscribers...")
    
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
              'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
              'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte']
    sources = ['website', 'booking', 'referral', 'social_media', 'event']
    
    for i in range(100):  # 100 fake subscribers
        cursor.execute('''
            INSERT INTO company_newsletter
            (name, phone, email, address, city, zipcode, last_activity_date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.name(),
            fake.phone_number(),
            fake.email(),
            fake.street_address(),
            random.choice(cities),
            fake.zipcode(),
            fake.date_between(start_date='-90d', end_date='today').strftime('%Y-%m-%d'),
            random.choice(sources)
        ))

def insert_fake_waitlist(cursor):
    """Insert fake waitlist data."""
    print("Creating fake waitlist entries...")
    
    time_slots = ['11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM', 
                  '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM', '8:00 PM']
    
    start_date = datetime.now()
    
    for i in range(15):  # 15 fake waitlist entries
        preferred_date = start_date + timedelta(days=random.randint(1, 14))
        
        cursor.execute('''
            INSERT INTO waitlist
            (name, phone, email, preferred_date, preferred_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            fake.name(),
            fake.phone_number(),
            fake.email(),
            preferred_date.strftime('%Y-%m-%d'),
            random.choice(time_slots),
            fake.date_time_between(start_date='-7d', end_date='now')
        ))

def insert_fake_activity_logs(cursor):
    """Insert fake activity log data."""
    print("Creating fake activity logs...")
    
    usernames = ['admin', 'superadmin', 'manager']
    action_types = ['BOOKING_CREATED', 'BOOKING_CANCELLED', 'DEPOSIT_CONFIRMED', 
                   'NEWSLETTER_SENT', 'WAITLIST_ADDED', 'WAITLIST_REMOVED', 
                   'USER_LOGIN', 'DATA_EXPORT']
    entity_types = ['BOOKING', 'NEWSLETTER', 'WAITLIST', 'USER']
    
    for i in range(200):  # 200 fake log entries
        action_type = random.choice(action_types)
        entity_type = random.choice(entity_types)
        
        # Make sure entity type matches action type somewhat logically
        if action_type.startswith('BOOKING'):
            entity_type = 'BOOKING'
        elif action_type.startswith('NEWSLETTER'):
            entity_type = 'NEWSLETTER'
        elif action_type.startswith('WAITLIST'):
            entity_type = 'WAITLIST'
        
        description = generate_activity_description(action_type, entity_type)
        
        cursor.execute('''
            INSERT INTO activity_logs
            (username, action_type, entity_type, entity_id, description, 
             reason, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            random.choice(usernames),
            action_type,
            entity_type,
            str(random.randint(1, 100)) if entity_type != 'NEWSLETTER' else None,
            description,
            generate_reason(action_type),
            fake.date_time_between(start_date='-30d', end_date='now'),
            generate_details(action_type, entity_type)
        ))

def generate_activity_description(action_type, entity_type):
    """Generate realistic activity descriptions."""
    descriptions = {
        'BOOKING_CREATED': f"New booking created for {fake.name()}",
        'BOOKING_CANCELLED': f"Booking cancelled for {fake.name()}",
        'DEPOSIT_CONFIRMED': f"Deposit confirmed for booking",
        'NEWSLETTER_SENT': f"Newsletter sent to {random.randint(50, 200)} recipients",
        'WAITLIST_ADDED': f"Customer {fake.name()} added to waitlist",
        'WAITLIST_REMOVED': f"Customer removed from waitlist",
        'USER_LOGIN': f"User logged into admin panel",
        'DATA_EXPORT': f"Data exported for analysis"
    }
    return descriptions.get(action_type, f"{action_type} performed")

def generate_reason(action_type):
    """Generate realistic reasons for actions."""
    reasons = {
        'BOOKING_CANCELLED': random.choice([
            "Customer requested cancellation",
            "Schedule conflict",
            "Payment issue",
            "Weather conditions"
        ]),
        'DEPOSIT_CONFIRMED': random.choice([
            "Payment received via bank transfer",
            "Cash payment confirmed",
            "Credit card payment processed",
            "Check payment cleared"
        ]),
        'NEWSLETTER_SENT': random.choice([
            "Monthly newsletter campaign",
            "Special promotion announcement",
            "Holiday greetings",
            "Service update notification"
        ]),
        'WAITLIST_REMOVED': random.choice([
            "Booking slot became available",
            "Customer no longer interested",
            "Duplicate entry removed"
        ])
    }
    return reasons.get(action_type, None)

def generate_details(action_type, entity_type):
    """Generate realistic details for activities."""
    if action_type == 'NEWSLETTER_SENT':
        return f"Subject: {fake.catch_phrase()}, Recipients: {random.randint(50, 200)}"
    elif action_type == 'BOOKING_CREATED':
        return f"Date: {fake.date_between(start_date='today', end_date='+30d')}, Time: {random.choice(['6:00 PM', '7:00 PM', '8:00 PM'])}"
    elif action_type == 'DEPOSIT_CONFIRMED':
        return f"Amount: ${random.randint(50, 500)}, Method: {random.choice(['Bank Transfer', 'Credit Card', 'Cash'])}"
    else:
        return None

if __name__ == "__main__":
    try:
        # Install faker if not already installed
        import faker
    except ImportError:
        print("Installing faker package...")
        import subprocess
        subprocess.check_call(["pip", "install", "faker"])
        import faker
    
    create_sample_database()
    print("Sample database creation completed!")
