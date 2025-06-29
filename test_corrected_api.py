#!/usr/bin/env python3
import requests

print('=== CORRECTED BACKEND TESTING ===')

# Test basic endpoints
try:
    print('1. Testing root endpoint...')
    response = requests.get('http://localhost:8000/')
    print(f'   Root: {response.status_code} - {response.text[:100]}')
except Exception as e:
    print(f'   Root: ERROR - {e}')

try:
    print('2. Testing availability endpoint...')
    response = requests.get('http://localhost:8000/api/booking/availability?date=2025-07-01')
    print(f'   Availability: {response.status_code} - {response.text[:100]}')
except Exception as e:
    print(f'   Availability: ERROR - {e}')

try:
    print('3. Testing login endpoint...')
    response = requests.post('http://localhost:8000/api/booking/token', 
        data={'username': 'ady', 'password': 'admin123'})
    print(f'   Login: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f'   ✓ Token received: {token[:30]}...' if token else '   No token')
        
        # Test protected endpoints with correct paths
        headers = {'Authorization': f'Bearer {token}'}
        
        print('4. Testing admin weekly endpoint...')
        response = requests.get('http://localhost:8000/api/booking/admin/weekly', headers=headers)
        print(f'   Admin weekly: {response.status_code}')
        
        print('5. Testing newsletter recipients endpoint...')
        response = requests.get('http://localhost:8000/api/booking/admin/newsletter/recipients', headers=headers)
        print(f'   Newsletter recipients: {response.status_code}')
        
        print('6. Testing superadmin list admins...')
        response = requests.get('http://localhost:8000/api/booking/superadmin/admins', headers=headers)
        print(f'   List admins: {response.status_code}')
        if response.status_code == 200:
            admins = response.json()
            print(f'   ✓ Found {len(admins)} admin(s)')
        
        print('7. Testing newsletter cities...')
        response = requests.get('http://localhost:8000/api/booking/admin/newsletter/cities', headers=headers)
        print(f'   Newsletter cities: {response.status_code}')
        
    else:
        print(f'   Login failed: {response.text}')
except Exception as e:
    print(f'   ERROR: {e}')

print('=== BACKEND TESTING COMPLETE ===')
