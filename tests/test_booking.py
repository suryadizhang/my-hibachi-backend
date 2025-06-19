import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from main import app
import pytest
import httpx
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_availability():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/booking/availability?date=2024-07-10")
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
            "date": test_date,
            "timeSlot": "12:00 PM",
            "contactPreference": "email"
        }
        # Book twice (should succeed)
        for _ in range(2):
            resp = await ac.post("/api/booking/book", json=payload)
            assert resp.status_code in (200, 201)
        # Third booking (should fail)
        resp = await ac.post("/api/booking/book", json=payload)
        assert resp.status_code == 400