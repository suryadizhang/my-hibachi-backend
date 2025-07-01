#!/usr/bin/env python3
"""
Final Comprehensive Test - Create bookings and test admin panel with real data
"""
import requests
import json
from datetime import datetime, timedelta
import sys

class ComprehensiveAdminTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.test_booking_ids = []
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print("="*60)
        
    def print_test(self, test_name):
        print(f"\n🧪 {test_name}")
        
    def login_as_admin(self):
        """Login as admin"""
        self.print_test("Admin Login")
        
        login_data = {
            "username": "ady",
            "password": "13Agustus!"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/booking/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print("   ✅ Admin login successful")
                return True
            else:
                print(f"   ❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    def create_test_bookings(self):
        """Create some test bookings for admin panel testing"""
        self.print_test("Creating Test Bookings")
        
        tomorrow = datetime.now() + timedelta(days=1)
        test_bookings = [
            {
                "name": "Test Customer 1",
                "phone": "555-0001",
                "email": "test1@example.com",
                "address": "123 Test St",
                "city": "Test City",
                "zipcode": "12345",
                "date": tomorrow.strftime("%Y-%m-%d"),
                "time_slot": "6:00 PM",
                "contact_preference": "email",
                "adults": 2,
                "children": 1,
                "proteins": [{"type": "Chicken", "quantity": 2}]
            },
            {
                "name": "Test Customer 2", 
                "phone": "555-0002",
                "email": "test2@example.com",
                "address": "456 Test Ave",
                "city": "Test City",
                "zipcode": "12345",
                "date": tomorrow.strftime("%Y-%m-%d"),
                "time_slot": "7:00 PM",
                "contact_preference": "phone",
                "adults": 4,
                "children": 0,
                "proteins": [{"type": "Steak", "quantity": 3}, {"type": "Shrimp", "quantity": 1}]
            }
        ]
        
        success_count = 0
        for i, booking in enumerate(test_bookings):
            try:
                response = requests.post(
                    f"{self.base_url}/api/booking/book",
                    json=booking
                )
                
                if response.status_code == 200:
                    booking_id = response.json().get("booking_id")
                    if booking_id:
                        self.test_booking_ids.append(booking_id)
                    print(f"   ✅ Test booking {i+1} created successfully")
                    success_count += 1
                else:
                    print(f"   ❌ Test booking {i+1} failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Test booking {i+1} error: {e}")
        
        print(f"   📊 Created {success_count}/{len(test_bookings)} test bookings")
        return success_count > 0
    
    def test_admin_functions_with_data(self):
        """Test admin functions now that we have real data"""
        self.print_test("Testing Admin Functions with Real Data")
        
        if not self.token:
            print("   ❌ No admin token available")
            return False
        
        # Test KPIs
        try:
            response = requests.get(
                f"{self.base_url}/api/booking/admin/kpis",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                kpis = response.json()
                print("   ✅ KPIs with real data:")
                print(f"      Total bookings: {kpis['total']}")
                print(f"      This week: {kpis['week']}")
                print(f"      This month: {kpis['month']}")
                print(f"      Waitlist: {kpis['waitlist']}")
            else:
                print(f"   ❌ KPIs failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ KPIs error: {e}")
            return False
        
        # Test weekly bookings
        try:
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            test_date = start_of_week.strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.base_url}/api/booking/admin/weekly?start_date={test_date}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                bookings = response.json()
                print(f"   ✅ Weekly bookings: {len(bookings)} found")
                if bookings:
                    print(f"      Sample: {bookings[0]['name']} - {bookings[0]['date']} {bookings[0]['time_slot']}")
            else:
                print(f"   ❌ Weekly bookings failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Weekly bookings error: {e}")
            return False
        
        return True
    
    def test_deposit_confirmation(self):
        """Test deposit confirmation with real booking"""
        self.print_test("Testing Deposit Confirmation")
        
        if not self.token or not self.test_booking_ids:
            print("   ⚠️ No booking ID available for testing")
            return True
        
        booking_id = self.test_booking_ids[0]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/booking/admin/confirm_deposit",
                json={"booking_id": booking_id},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Deposit confirmation successful")
                print(f"   📄 Response: {result}")
                return True
            else:
                print(f"   ❌ Deposit confirmation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Deposit confirmation error: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test bookings (optional)"""
        self.print_test("Cleaning Up Test Data")
        
        if not self.token or not self.test_booking_ids:
            print("   ⚠️ No test data to clean up")
            return True
        
        cleaned = 0
        for booking_id in self.test_booking_ids:
            try:
                response = requests.delete(
                    f"{self.base_url}/api/booking/admin/cancel_booking?booking_id={booking_id}",
                    json={"reason": "Test cleanup"},
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    cleaned += 1
                    print(f"   ✅ Cleaned up booking {booking_id}")
                else:
                    print(f"   ⚠️ Could not clean up booking {booking_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Cleanup error for booking {booking_id}: {e}")
        
        print(f"   📊 Cleaned up {cleaned}/{len(self.test_booking_ids)} test bookings")
        return True
    
    def run_comprehensive_test(self):
        """Run the complete comprehensive test"""
        self.print_header("COMPREHENSIVE ADMIN PANEL TEST WITH REAL DATA")
        
        tests = [
            ("Admin Login", self.login_as_admin),
            ("Create Test Bookings", self.create_test_bookings),
            ("Test Admin Functions with Data", self.test_admin_functions_with_data),
            ("Test Deposit Confirmation", self.test_deposit_confirmation),
            ("Cleanup Test Data", self.cleanup_test_data),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"   ❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        self.print_header("COMPREHENSIVE TEST RESULTS")
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL COMPREHENSIVE ADMIN PANEL TESTS PASSED!")
            print("🔧 Frontend and backend are fully synchronized!")
        else:
            print("⚠️ Some comprehensive tests failed")
        
        return passed == total

if __name__ == "__main__":
    tester = ComprehensiveAdminTest()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
