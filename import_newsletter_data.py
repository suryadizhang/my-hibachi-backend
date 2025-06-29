#!/usr/bin/env python3
"""
Import customer data from CSV into the newsletter database
This script processes the customer database with geography and imports it into the newsletter system
"""
import csv
import sqlite3
import re
from datetime import datetime
from pathlib import Path

def clean_phone(phone_str):
    """Clean and format phone number"""
    if not phone_str or phone_str.strip().lower() == 'unknown':
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_str)
    # Format as (XXX) XXX-XXXX if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone_str.strip()

def clean_email(email_str):
    """Clean and validate email"""
    if not email_str or email_str.strip().lower() == 'unknown':
        return None
    email = email_str.strip()
    # Basic email validation
    if '@' in email and '.' in email:
        return email
    return None

def extract_city_from_address(address_str):
    """Extract city from address string"""
    if not address_str:
        return None
    
    # Common patterns: "Address, City, State ZIP" or "Address City State ZIP"
    # Split by comma first
    parts = address_str.split(',')
    if len(parts) >= 2:
        # Take the part before the last comma as potential city
        city_part = parts[-2].strip()
        # Remove state and ZIP from city part
        city_clean = re.sub(r'\s+(CA|ID|NM)\s+\d{5}.*$', '', city_part).strip()
        return city_clean if city_clean else None
    
    # If no comma, try to extract city before state abbreviation
    match = re.search(r'(.+?)\s+(CA|ID|NM)\s+\d{5}', address_str)
    if match:
        # Get the last word before state as city
        city_part = match.group(1).strip()
        words = city_part.split()
        if len(words) >= 2:
            return words[-1]
    
    return None


def extract_state_from_address(address_str):
    """Extract state from address string"""
    if not address_str:
        return None
    
    # Look for state abbreviations
    state_match = re.search(r'\b(CA|ID|NM)\b', address_str)
    if state_match:
        state_abbr = state_match.group(1)
        # Convert to full state name
        state_map = {
            'CA': 'California',
            'ID': 'Idaho', 
            'NM': 'New Mexico'
        }
        return state_map.get(state_abbr, state_abbr)
    
    return None

def parse_date(date_str):
    """Parse and normalize date string"""
    if not date_str or date_str.strip().lower() == 'unknown':
        return None
    
    date_str = date_str.strip()
    
    # Try different date formats
    formats = [
        "%B %d, %Y",  # March 22, 2025
        "%b %d, %Y",  # Mar 22, 2025
        "%B %d",      # March 22
        "%b %d",      # Mar 22
        "%Y-%m-%d",   # 2025-03-22
    ]
    
    for fmt in formats:
        try:
            if fmt in ["%B %d", "%b %d"]:
                # Add current year for dates without year
                parsed = datetime.strptime(f"{date_str}, 2025", f"{fmt}, %Y")
            else:
                parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Handle special cases
    if "October" in date_str and "2024" in date_str:
        try:
            return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
        except:
            pass
    
    return date_str  # Return as-is if can't parse

def import_customer_data():
    """Import customer data from CSV to newsletter database"""
    csv_file = Path(__file__).parent / "customer database with geography.csv"
    db_file = Path(__file__).parent / "mh-bookings.db"
    
    if not csv_file.exists():
        print(f"Error: CSV file not found at {csv_file}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # First, check if we need to add missing columns to existing table
    c.execute("PRAGMA table_info(company_newsletter)")
    existing_columns = [col[1] for col in c.fetchall()]
    
    # Add missing columns if they don't exist
    required_columns = {
        'state': 'TEXT',
        'geographic_region': 'TEXT', 
        'booking_history': 'TEXT'
    }
    
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE company_newsletter ADD COLUMN {column_name} {column_type}")
                print(f"✓ Added missing column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Note: Column {column_name} may already exist: {e}")
    
    # Handle created_at separately since SQLite doesn't support adding columns with non-constant defaults
    if 'created_at' not in existing_columns:
        try:
            c.execute(f"ALTER TABLE company_newsletter ADD COLUMN created_at TEXT")
            print(f"✓ Added missing column: created_at")
        except sqlite3.OperationalError as e:
            print(f"Note: Column created_at may already exist: {e}")
    
    conn.commit()
    
    # Read and process CSV
    imported = 0
    skipped = 0
    errors = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                # Extract and clean data
                name = row['Name'].strip() if row['Name'] else None
                phone = clean_phone(row['Phone Number'])
                email = clean_email(row['Email Address'])
                address = row['Address'].strip() if row['Address'] else None
                city = extract_city_from_address(address) if address else None
                state = extract_state_from_address(address) if address else None
                
                # Extract ZIP code from address
                zipcode = None
                if address:
                    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
                    if zip_match:
                        zipcode = zip_match.group(1)
                
                last_activity = parse_date(row['Latest Date of Event'])
                booking_history = row['Booking History'].strip() if row['Booking History'] else None
                geographic_region = row['Geographic Region'].strip() if row['Geographic Region'] else None
                
                # Skip if no name or (no email and no phone)
                if not name or (not email and not phone):
                    print(f"Skipping row {reader.line_num}: name='{name}', email='{email}', phone='{phone}'")
                    skipped += 1
                    continue
                
                # Insert into database
                c.execute("""
                    INSERT INTO company_newsletter 
                    (name, phone, email, address, city, state, zipcode, 
                     last_activity_date, source, geographic_region, 
                     booking_history, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    phone,
                    email,
                    address,
                    city,
                    state,
                    zipcode,
                    last_activity,
                    'CSV Import',
                    geographic_region,
                    booking_history,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                
                imported += 1
                
            except Exception as e:
                print(f"Error processing row {reader.line_num}: {e}")
                print(f"Row data: {row}")
                errors += 1
                continue
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Import Results ===")
    print(f"✓ Successfully imported: {imported} customers")
    print(f"⚠ Skipped (missing data): {skipped} customers")
    print(f"✗ Errors: {errors} customers")
    print(f"📊 Total processed: {imported + skipped + errors} rows")
    
    return True

def verify_import():
    """Verify the imported data"""
    db_file = Path(__file__).parent / "mh-bookings.db"
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM company_newsletter")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM company_newsletter WHERE email IS NOT NULL AND email != ''")
    with_email = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM company_newsletter WHERE phone IS NOT NULL AND phone != ''")
    with_phone = c.fetchone()[0]
    
    # Check geographic regions
    try:
        c.execute("SELECT DISTINCT geographic_region FROM company_newsletter WHERE geographic_region IS NOT NULL")
        regions = [row[0] for row in c.fetchall()]
    except sqlite3.OperationalError:
        regions = []
    
    # Check states
    try:
        c.execute("SELECT DISTINCT state FROM company_newsletter WHERE state IS NOT NULL")
        states = [row[0] for row in c.fetchall()]
    except sqlite3.OperationalError:
        states = []
    
    c.execute("SELECT DISTINCT city FROM company_newsletter WHERE city IS NOT NULL ORDER BY city LIMIT 10")
    cities = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    print("\n=== Newsletter Database Verification ===")
    print(f"📧 Total customers: {total}")
    print(f"✉️ With email addresses: {with_email}")
    print(f"📞 With phone numbers: {with_phone}")
    if regions:
        print(f"🌍 Geographic regions: {', '.join(regions)}")
    if states:
        print(f"🗺️ States: {', '.join(states)}")
    print(f"🏙️ Sample cities: {', '.join(cities[:5])}...")
    
    return total > 0

if __name__ == "__main__":
    print("=== My Hibachi Newsletter Database Import ===")
    print("Importing customer data from CSV...")
    
    if import_customer_data():
        print("\n✓ Import completed successfully!")
        verify_import()
    else:
        print("\n✗ Import failed!")
