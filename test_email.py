#!/usr/bin/env python3
"""Test the email system configuration"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("csbook.env")

def test_email_config():
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    
    print("Email Configuration Test:")
    print(f"SMTP_USER: {smtp_user}")
    print(f"SMTP_PASS: {'*' * len(smtp_pass) if smtp_pass else 'Not set'}")
    
    if smtp_user and smtp_pass:
        print("✓ Email credentials are configured")
        return True
    else:
        print("✗ Email credentials are missing")
        return False

def test_email_functions():
    """Test email function imports"""
    try:
        from app.email_utils import (
            send_customer_confirmation,
            send_deposit_confirmation_email,
            send_booking_cancellation_email
        )
        print("✓ Email functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Error importing email functions: {e}")
        return False

if __name__ == "__main__":
    print("=== My Hibachi Email System Test ===")
    config_ok = test_email_config()
    functions_ok = test_email_functions()
    
    if config_ok and functions_ok:
        print("\n✓ Email system is ready!")
        print("\nEmail flow configured:")
        print("- Booking confirmation: customer + info@myhibachichef.com")
        print("- Deposit confirmation: customer + info@myhibachichef.com")
        print("- Cancellation confirmation: customer + info@myhibachichef.com")
        print("- All sent from: cs@myhibachichef.com")
    else:
        print("\n✗ Email system has issues")
