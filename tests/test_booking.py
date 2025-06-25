import sys
import os
import glob
import pytest

# Clean up the test DB before running tests
def setup_module(module):
    db_dir = os.path.join(os.path.dirname(__file__), "../weekly_databases")
    for f in glob.glob(os.path.join(db_dir, "*.db")):
        os.remove(f)
    # Remove mh-bookings.db if it exists
    main_db = os.path.join(os.path.dirname(__file__), "..", "mh-bookings.db")
    if os.path.exists(main_db):
        os.remove(main_db)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from main import app
import httpx
from datetime import datetime, timedelta

# Mock email sending for all tests in this module
@pytest.fixture(autouse=True)
def patch_send_email(monkeypatch):
    from app import email_utils
    monkeypatch.setattr(email_utils, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_booking_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_customer_confirmation", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_waitlist_confirmation", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_cancellation_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_waitlist_slot_opened", lambda *args, **kwargs: None)

@pytest.mark.asyncio
async def test_availability():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/availability?date=2024-07-10")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

@pytest.mark.asyncio
async def test_booking_and_fully_booked():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        test_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        payload = {
            "name": "Test User",
            "phone": "1234567890",
            "email": "test@example.com",
            "address": "123 Test St",
            "city": "Testville",
            "zipcode": "12345",
            "date": test_date,
            "time_slot": "12:00 PM",
            "contact_preference": "email"
        }
        # First booking should succeed
        resp = await ac.post("/book", json=payload)
        print(resp.status_code, resp.json())
        assert resp.status_code in (200, 201)
        # Second booking should succeed
        resp = await ac.post("/book", json=payload)
        print(resp.status_code, resp.json())
        assert resp.status_code in (200, 201)
        # Third booking should fail
        resp = await ac.post("/book", json=payload)
        print(resp.status_code, resp.json())
        assert resp.status_code == 400
        assert resp.json().get("detail") == "This slot is fully booked."