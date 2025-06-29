#!/usr/bin/env python3
"""
Test the email cleaning function
"""
from import_newsletter_data import clean_email

def test_email_cleaning():
    print("Testing email cleaning function:")
    
    # Test cases
    test_cases = [
        ("test@example.com", "Valid email"),
        ("", "Empty email"), 
        ("unknown", "Unknown email"),
        ("notanemail", "Invalid email"),
        (None, "None email"),
        ("  user@domain.com  ", "Email with spaces")
    ]
    
    for email_input, description in test_cases:
        result = clean_email(email_input)
        print(f"  {description}: '{email_input}' -> {result}")

if __name__ == "__main__":
    test_email_cleaning()
