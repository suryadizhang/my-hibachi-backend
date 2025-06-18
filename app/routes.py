from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime, timedelta
from .database import get_week_db, DB_DIR
import os
import sqlite3

router = APIRouter()

# Use a strong, secret API key (store in env variable in production)
ADMIN_API_KEY = "REPLACE_WITH_A_LONG_RANDOM_SECRET"

def admin_auth(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/book")
def book_service(data: dict):
    # Validate input (add more as needed)
    required = ["name", "phone", "email", "address", "date", "timeSlot", "contactPreference"]
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(status_code=400, detail=f"Missing {field}")
    # Save to weekly DB
    conn, _ = get_week_db(data["date"])
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings (name, phone, email, address, date, time_slot, contact_preference, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["phone"], data["email"], data["address"],
        data["date"], data["timeSlot"], data["contactPreference"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    return {"message": "Booking successful"}

@router.get("/admin/weekly", dependencies=[Depends(admin_auth)])
def admin_weekly(start_date: str):
    try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    year, week, _ = date.isocalendar()
    db_path = os.path.join(DB_DIR, f"bookings_{year}-{week:02d}.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM bookings ORDER BY date, time_slot, created_at")
    return [dict(row) for row in c.fetchall()]

@router.get("/admin/monthly", dependencies=[Depends(admin_auth)])
def admin_monthly(year: int, month: int):
    from calendar import monthrange
    from datetime import date as dt_date
    first_day = dt_date(year, month, 1)
    last_day = dt_date(year, month, monthrange(year, month)[1])
    week_files = set()
    day = first_day
    while day <= last_day:
        y, w, _ = day.isocalendar()
        week_files.add((y, w))
        day += timedelta(days=1)
    bookings = []
    for y, w in week_files:
        db_path = os.path.join(DB_DIR, f"bookings_{y}-{w:02d}.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM bookings WHERE date BETWEEN ? AND ? ORDER BY date, time_slot, created_at",
                      (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))
            bookings.extend([dict(row) for row in c.fetchall()])
    return bookings