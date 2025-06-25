from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_send_email(monkeypatch):
    from app import email_utils
    monkeypatch.setattr(email_utils, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_booking_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_customer_confirmation", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_waitlist_confirmation", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_cancellation_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_utils, "send_waitlist_slot_opened", lambda *args, **kwargs: None)

def test_availability():
    response = client.get("/availability?date=2025-07-01")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_book_rate_limit():
    data = {
        "name": "Test User",
        "phone": "1234567890",
        "email": "test@example.com",
        "address": "123 Test St",
        "city": "Testville",
        "zipcode": "12345",
        "date": "2025-07-01",
        "time_slot": "12:00 PM",
        "contact_preference": "email"
    }
    for _ in range(5):
        client.post("/book", json=data)
    # 6th request should be rate limited
    response = client.post("/book", json=data)
    assert response.status_code == 429