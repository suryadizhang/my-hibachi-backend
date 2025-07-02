"""
Simple script to test admin login flow and check results
"""

print("""
🔧 ADMIN PANEL DEBUG INSTRUCTIONS
======================================

1. Open your browser to: http://localhost:5176/admin-login

2. Open Developer Tools (F12) and go to Console tab

3. Login with:
   Username: test_superadmin
   Password: TestPass123!

4. After login, check the admin panel page for:
   - DEBUG INFO panel showing current state
   - Console logs starting with "AdminPanel:"
   - KPI cards showing numbers
   - Any error messages

5. Expected values:
   - KPIs: Total=50, Week=23, Month=0, Waitlist=3
   - Bookings: Should load 49 upcoming bookings
   - Mode: upcoming
   - Loading: Should be No after data loads

6. If you see issues, check the Console tab for:
   - Network errors (red entries)
   - JavaScript errors
   - AdminPanel log messages

7. Common issues to look for:
   - CORS errors
   - 401 Unauthorized (token issues)
   - Network timeout
   - React re-render loops
   - Component mount/unmount issues

======================================
🎯 Quick Status Check:
""")

# Quick backend status check
import requests

try:
    # Test if backend is running
    response = requests.get("http://localhost:8000/api/booking", timeout=5)
    print("✅ Backend is running")
except:
    print("❌ Backend is not responding - start it with 'python main.py'")

try:
    # Test if frontend is running  
    response = requests.get("http://localhost:5176", timeout=5)
    print("✅ Frontend is running")
except:
    print("❌ Frontend is not responding - start it with 'npm run dev'")

print("\n💡 If both servers are running, the issue is likely in the browser console.")
print("💡 Check for JavaScript errors or failed network requests.")
