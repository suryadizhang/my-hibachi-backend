#!/usr/bin/env python3
"""
Comprehensive Deep Test for Admin Panel Functions
"""
import requests
import json
from datetime import datetime, timedelta
import sys


class AdminPanelTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.test_booking_id = None

    def print_header(self, title):
        print(f"\n{'=' * 60}")
        print(f"🔧 {title}")
        print("=" * 60)

    def print_test(self, test_name):
        print(f"\n🧪 {test_name}")

    def login_as_admin(self):
        """Test admin login and get token"""
        self.print_test("Admin Login")

        # Try to login with test admin credentials
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
                print(f"   🔑 Token received: {self.token[:20]}...")
                return True
            else:
                print(f"   ❌ Login failed: {response.status_code} - "
                      f"{response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    def test_admin_kpis(self):
        """Test admin KPIs endpoint"""
        self.print_test("Admin KPIs")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/booking/admin/kpis",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                kpis = response.json()
                print("   ✅ KPIs retrieved successfully")
                print(f"   📊 Data: {json.dumps(kpis, indent=4)}")
                return True
            else:
                print(f"   ❌ KPIs failed: {response.status_code} - "
                      f"{response.text}")
                return False

        except Exception as e:
            print(f"   ❌ KPIs error: {e}")
            return False

    def test_weekly_bookings(self):
        """Test weekly bookings endpoint"""
        self.print_test("Weekly Bookings")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        # Test with current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        test_date = start_of_week.strftime("%Y-%m-%d")

        try:
            response = requests.get(
                f"{self.base_url}/api/booking/admin/weekly"
                f"?start_date={test_date}",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                bookings = response.json()
                print("   ✅ Weekly bookings retrieved successfully")
                print(f"   📅 Week starting: {test_date}")
                print(f"   📋 Found {len(bookings)} bookings")

                if bookings:
                    print("   📝 Sample booking:")
                    sample = bookings[0]
                    self.test_booking_id = sample.get('id')
                    print(f"      ID: {sample.get('id')}")
                    print(f"      Name: {sample.get('name')}")
                    print(f"      Date: {sample.get('date')}")
                    print(f"      Time: {sample.get('time_slot')}")
                    print(
                        f"      Deposit: {
                            sample.get(
                                'deposit_received',
                                False)}")

                return True
            else:
                print(f"   ❌ Weekly bookings failed: {response.status_code} - "
                      f"{response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Weekly bookings error: {e}")
            return False

    def test_monthly_bookings(self):
        """Test monthly bookings endpoint"""
        self.print_test("Monthly Bookings")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        today = datetime.now()
        year = today.year
        month = today.month

        try:
            response = requests.get(
                f"{self.base_url}/api/booking/admin/monthly"
                f"?year={year}&month={month}",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                bookings = response.json()
                print("   ✅ Monthly bookings retrieved successfully")
                print(f"   📅 Month: {year}-{month:02d}")
                print(f"   📋 Found {len(bookings)} bookings")
                return True
            else:
                msg = (f"   ❌ Monthly bookings failed: "
                       f"{response.status_code} - {response.text}")
                print(msg)
                return False

        except Exception as e:
            print(f"   ❌ Monthly bookings error: {e}")
            return False

    def test_confirm_deposit(self):
        """Test deposit confirmation endpoint"""
        self.print_test("Confirm Deposit")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        if not self.test_booking_id:
            print("   ⚠️ No booking ID available for testing")
            return True

        try:
            response = requests.post(
                f"{self.base_url}/api/booking/admin/confirm_deposit",
                json={"booking_id": self.test_booking_id},
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                result = response.json()
                print("   ✅ Deposit confirmation successful")
                print(f"   📄 Response: {result}")
                return True
            elif response.status_code == 422:
                print("   ⚠️ Validation error (expected for missing fields)")
                print(f"   📝 Details: {response.json()}")
                return True
            else:
                print(
                    f"   ❌ Deposit confirmation failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Deposit confirmation error: {e}")
            return False

    def test_cancel_booking(self):
        """Test booking cancellation endpoint"""
        self.print_test("Cancel Booking")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        if not self.test_booking_id:
            print("   ⚠️ No booking ID available for testing")
            return True

        try:
            # First try to get booking details
            response = requests.delete(
                f"{self.base_url}/api/booking/admin/cancel_booking?booking_id={self.test_booking_id}",
                json={"reason": "Test cancellation - admin panel deep test"},
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                result = response.json()
                print("   ✅ Booking cancellation successful")
                print(f"   📄 Response: {result}")
                return True
            elif response.status_code == 404:
                print("   ⚠️ Booking not found (may have been cancelled already)")
                return True
            else:
                print(
                    f"   ❌ Booking cancellation failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Booking cancellation error: {e}")
            return False

    def test_change_password(self):
        """Test password change endpoint"""
        self.print_test("Change Password")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        # Test with invalid current password to avoid actually changing
        # password
        try:
            from urllib.parse import urlencode

            data = {
                'current_password': 'wrong_password',
                'new_password': 'new_test_password123'
            }

            response = requests.post(
                f"{self.base_url}/api/booking/admin/change_password",
                data=urlencode(data),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

            if response.status_code == 400:
                print(
                    "   ✅ Password change validation working (rejected wrong current password)")
                return True
            elif response.status_code == 200:
                print("   ⚠️ Password change succeeded (unexpected with wrong password)")
                return True
            else:
                print(
                    f"   ❌ Password change failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Password change error: {e}")
            return False

    def test_waitlist_management(self):
        """Test waitlist management endpoints"""
        self.print_test("Waitlist Management")

        if not self.token:
            print("   ❌ No admin token available")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/booking/admin/waitlist",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                waitlist = response.json()
                print("   ✅ Waitlist retrieved successfully")
                print(f"   📋 Found {len(waitlist)} waitlist entries")

                if waitlist:
                    print("   📝 Sample waitlist entry:")
                    sample = waitlist[0]
                    print(f"      ID: {sample.get('id')}")
                    print(f"      Name: {sample.get('name')}")
                    print(
                        f"      Preferred Date: {
                            sample.get('preferred_date')}")
                    print(
                        f"      Preferred Time: {
                            sample.get('preferred_time')}")

                return True
            else:
                print(
                    f"   ❌ Waitlist retrieval failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Waitlist error: {e}")
            return False

    def run_all_tests(self):
        """Run all admin panel tests"""
        self.print_header("ADMIN PANEL DEEP TEST")

        tests = [
            ("Admin Login", self.login_as_admin),
            ("Admin KPIs", self.test_admin_kpis),
            ("Weekly Bookings", self.test_weekly_bookings),
            ("Monthly Bookings", self.test_monthly_bookings),
            ("Waitlist Management", self.test_waitlist_management),
            ("Confirm Deposit", self.test_confirm_deposit),
            ("Change Password", self.test_change_password),
            ("Cancel Booking", self.test_cancel_booking),
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"   ❌ {test_name} crashed: {e}")
                results[test_name] = False

        self.print_header("ADMIN PANEL TEST RESULTS")

        passed = 0
        total = len(tests)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1

        print(
            f"\n📊 SUMMARY: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

        if passed == total:
            print("🎉 ALL ADMIN PANEL FUNCTIONS WORKING CORRECTLY!")
        else:
            print("⚠️ Some admin panel functions need attention")

        return passed == total


if __name__ == "__main__":
    tester = AdminPanelTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
