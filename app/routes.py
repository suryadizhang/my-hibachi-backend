from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .database import get_week_db, get_user_db
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sqlite3
from .models import BookingCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/booking/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    conn = get_user_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (payload["sub"],))
    user = c.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def superadmin_required(user=Depends(get_current_user)):
    if user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin privileges required")
    return user

def admin_required(user=Depends(get_current_user)):
    if user["role"] not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_user_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    user = c.fetchone()
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/superadmin/create_admin")
def create_admin(username: str, password: str, user=Depends(superadmin_required)):
    conn = get_user_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  (username, hash_password(password), "admin"))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Admin created"}

@router.post("/book", status_code=status.HTTP_201_CREATED)
def book_service(data: BookingCreate):
    """Create a new booking."""
    conn = get_week_db(data.date)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?", (data.date, data.timeSlot))
    if c.fetchone()[0] >= 2:
        raise HTTPException(status_code=400, detail="This slot is fully booked.")
    c.execute("""
        INSERT INTO bookings (name, phone, email, address, date, time_slot, contact_preference, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.name, data.phone, data.email, data.address,
        data.date, data.timeSlot, data.contactPreference,
        datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    ))
    conn.commit()
    return {"message": "Booking successful"}

@router.get("/admin/weekly")
def admin_weekly(start_date: str, user=Depends(admin_required)):
    try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    year, week, _ = date.isocalendar()
    db_path = os.path.join("backend/weekly_databases", f"bookings_{year}-{week:02d}.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM bookings ORDER BY date, time_slot, created_at")
    return [dict(row) for row in c.fetchall()]

@router.get("/admin/monthly")
def admin_monthly(year: int, month: int, user=Depends(admin_required)):
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
        db_path = os.path.join("backend/weekly_databases", f"bookings_{y}-{w:02d}.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM bookings WHERE date BETWEEN ? AND ? ORDER BY date, time_slot, created_at",
                      (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))
            bookings.extend([dict(row) for row in c.fetchall()])
    return bookings

@router.get("/availability")
def get_availability(date: str):
    """
    Returns the number of bookings for each time slot on the given date.
    """
    conn = get_week_db(date)
    c = conn.cursor()
    c.execute(
        "SELECT time_slot, COUNT(*) as count FROM bookings WHERE date = ? GROUP BY time_slot",
        (date,)
    )
    slots = {row["time_slot"]: row["count"] for row in c.fetchall()}
    # List all possible slots
    all_slots = ['12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM']
    return {slot: slots.get(slot, 0) for slot in all_slots}