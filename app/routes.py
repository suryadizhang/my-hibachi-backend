from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .database import get_week_db, get_user_db
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sqlite3
from .email_utils import (
    send_booking_email,
    send_customer_confirmation,
    send_waitlist_confirmation,
    send_cancellation_email,
    send_email,
    send_waitlist_slot_opened,
)
from .models import BookingCreate, WaitlistCreate, CancelBookingRequest, WaitlistEntry
import logging
import threading
import time
from .deposit_tasks import schedule_deposit_jobs
from .utils import get_latest_user_info, upsert_newsletter_entry, notify_all_waitlist_users
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

router = APIRouter()

# Use limiter from app.state in your endpoints
# @limiter.limit("5/minute")
# def your_endpoint(...):
#     ...

logger = logging.getLogger("booking")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/booking/token")
limiter = Limiter(key_func=get_remote_address)

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
    """Authenticate user and return a JWT access token."""
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
    """Create a new admin user (superadmin only)."""
    conn = get_user_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  (username, hash_password(password), "admin"))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Admin created"}

@router.post("/book")
@limiter.limit("5/minute")
def book_service(data: BookingCreate, background_tasks: BackgroundTasks, request: Request):
    """Create a new booking and send confirmation emails."""
    conn = get_week_db(data.date)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?", (data.date, data.time_slot))
    count = c.fetchone()[0]
    print(f"DEBUG: Booking count for {data.date} {data.time_slot}: {count}")  # <-- Add this line
    if count >= 2:
        raise HTTPException(status_code=400, detail="This slot is fully booked.")
    c.execute("""
        INSERT INTO bookings (name, phone, email, address, city, zipcode, date, time_slot, contact_preference, created_at, deposit_received)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.name, data.phone, data.email, data.address, data.city, data.zipcode,
        data.date, data.time_slot, data.contact_preference,
        datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
        0  # deposit_received
    ))
    booking_id = c.lastrowid
    conn.commit()
    background_tasks.add_task(send_booking_email, data)
    background_tasks.add_task(send_customer_confirmation, data)
    schedule_deposit_jobs(booking_id, data.date)
    # Upsert newsletter entry
    upsert_newsletter_entry(data.model_dump(), "booking")
    return {"message": "Booking successful"}

# Example for any admin route in app/routes.py
@router.get("/admin/weekly")
def admin_weekly(start_date: str, user=Depends(admin_required)):
    """Get all bookings for a given week (admin only)."""
    try:
        date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    year, week, _ = date.isocalendar()
    db_path = os.path.join("backend/weekly_databases", f"bookings_{year}-{week:02d}.db")
    if not os.path.exists(db_path):
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM bookings ORDER BY date, time_slot, created_at")
        return [dict(row) for row in c.fetchall()]

@router.get("/admin/monthly")
def admin_monthly(year: int, month: int, user=Depends(admin_required)):
    """Get all bookings for a given month (admin only)."""
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
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM bookings WHERE date BETWEEN ? AND ? ORDER BY date, time_slot, created_at",
                          (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))
                bookings.extend([dict(row) for row in c.fetchall()])
    return bookings

@router.get("/availability")
def get_availability(date: str):
    """Get availability status for each time slot on a given date."""
    conn = get_week_db(date)
    c = conn.cursor()
    c.execute(
        "SELECT time_slot, COUNT(*) as count FROM bookings WHERE date = ? GROUP BY time_slot",
        (date,)
    )
    slots = {row["time_slot"]: row["count"] for row in c.fetchall()}
    all_slots = ['12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM']
    result = {}
    for slot in all_slots:
        count = slots.get(slot, 0)
        if count == 0:
            status = "available"
        elif count == 1:
            status = "waiting"
        else:
            status = "booked"
        result[slot] = {"status": status}
    return result

@router.post("/waitlist")
@limiter.limit("10/minute")  # 10 waitlist joins per minute per IP
def join_waitlist(data: WaitlistCreate, background_tasks: BackgroundTasks, request: Request):
    """Add a user to the waitlist, send confirmation and position email."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO waitlist (name, phone, email, preferred_date, preferred_time)
            VALUES (?, ?, ?, ?, ?)
        """, (data.name, data.phone, data.email, data.preferred_date, data.preferred_time))
        conn.commit()
        # Get the user's position in the waitlist for this slot
        c.execute("""
            SELECT id FROM waitlist
            WHERE preferred_date = ? AND preferred_time = ?
            ORDER BY created_at
        """, (data.preferred_date, data.preferred_time))
        ids = [row[0] for row in c.fetchall()]
        position = ids.index(c.lastrowid) + 1 if c.lastrowid in ids else len(ids)
    background_tasks.add_task(send_waitlist_confirmation, data.dict())
    background_tasks.add_task(send_waitlist_position_email, data.dict(), position)
    # Upsert newsletter entry
    upsert_newsletter_entry(data.dict(), "waitlist")
    return {"message": f"Added to waitlist. You are number {position} in line."}

@router.delete("/admin/cancel_booking")
def cancel_booking(
    booking_id: int,
    body: CancelBookingRequest = Body(...),
    user=Depends(admin_required)
):
    """Cancel a booking by ID, send cancellation email, and log the action (admin only)."""
    reason = body.reason
    db_folder = "backend/weekly_databases"
    found = False
    cancelled_booking = None
    for db_file in os.listdir(db_folder):
        if db_file.endswith(".db"):
            db_path = os.path.join(db_folder, db_file)
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
                booking = c.fetchone()
                if booking:
                    c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
                    conn.commit()
                    found = True
                    cancelled_booking = dict(booking)
                    logger.info(f"Admin {user['username']} cancelled booking {booking_id} for reason: {reason}")
                    try:
                        send_cancellation_email(cancelled_booking, reason)
                    except Exception as e:
                        logger.error(f"Failed to send cancellation email: {e}")
                    # Notify the first user on the waitlist for this slot
                    notify_all_waitlist_users(booking["date"], booking["time_slot"], send_waitlist_slot_opened)
                    break
    if not found:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking cancelled", "booking": cancelled_booking}

@router.post("/admin/confirm_deposit")
def confirm_deposit(booking_id: int, date: str, user=Depends(admin_required)):
    """Admin marks a booking as deposit received."""
    conn = get_week_db(date)
    c = conn.cursor()
    c.execute("UPDATE bookings SET deposit_received = 1 WHERE id = ?", (booking_id,))
    if c.rowcount == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    conn.commit()
    # Optionally: Remove scheduled jobs for this booking
    from .deposit_tasks import scheduler
    scheduler.remove_job(f"reminder_{booking_id}")
    scheduler.remove_job(f"admin_notify_{booking_id}")
    return {"message": "Deposit confirmed"}

@router.get("/admin/waitlist", response_model=list[WaitlistEntry])
def get_waitlist(user=Depends(admin_required)):
    """
    Get all waitlist entries, sorted by preferred_date, preferred_time, and created_at (admin only).
    """
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM waitlist ORDER BY preferred_date, preferred_time, created_at")
        waitlist = [dict(row) for row in c.fetchall()]
    return waitlist

@router.delete("/admin/waitlist/{waitlist_id}")
def remove_waitlist_user(waitlist_id: int, user=Depends(admin_required)):
    """
    Admin removes a user from the waitlist by ID.
    """
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM waitlist WHERE id = ?", (waitlist_id,))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Waitlist entry not found")
        conn.commit()
    return {"message": f"Waitlist entry {waitlist_id} removed."}

@router.post("/admin/waitlist/{waitlist_id}/move_to_booking")
def move_waitlist_to_booking(waitlist_id: int, user=Depends(admin_required)):
    """
    Admin moves a user from the waitlist to the bookings table (if slot is available).
    Fetches user info from previous bookings if available, and notifies the user.
    """
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM waitlist WHERE id = ?", (waitlist_id,))
        entry = c.fetchone()
        if not entry:
            raise HTTPException(status_code=404, detail="Waitlist entry not found")
        # Use utility to fetch latest info
        address, city, zipcode, contact_preference = get_latest_user_info(entry["email"])
        c.execute(
            "SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?",
            (entry["preferred_date"], entry["preferred_time"])
        )
        if c.fetchone()[0] >= 2:
            raise HTTPException(status_code=400, detail="Slot is fully booked")
        booking_data = {
            "name": entry["name"],
            "phone": entry["phone"],
            "email": entry["email"],
            "address": address,
            "city": city,
            "zipcode": zipcode,
            "date": entry["preferred_date"],
            "time_slot": entry["preferred_time"],
            "contact_preference": contact_preference,
        }
        c.execute("""
            INSERT INTO bookings (name, phone, email, address, city, zipcode, date, time_slot, contact_preference, created_at, deposit_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 0)
        """, (
            booking_data["name"], booking_data["phone"], booking_data["email"], booking_data["address"],
            booking_data["city"], booking_data["zipcode"], booking_data["date"], booking_data["time_slot"],
            booking_data["contact_preference"]
        ))
        c.execute("DELETE FROM waitlist WHERE id = ?", (waitlist_id,))
        conn.commit()
    # Send booking confirmation email to user
    send_customer_confirmation(type("Booking", (), booking_data))
    # Upsert newsletter entry
    upsert_newsletter_entry(booking_data, "booking")
    return {"message": f"Waitlist entry {waitlist_id} moved to bookings and user notified."}

@router.get("/admin/newsletter/export")
def export_newsletter(user=Depends(admin_required)):
    """Export all company newsletter contacts as CSV (admin only)."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT name, phone, email, address, city, zipcode, last_activity_date, source FROM company_newsletter")
        rows = c.fetchall()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "address", "city", "zipcode", "last_activity_date", "source"])
    for row in rows:
        writer.writerow([row["name"], row["phone"], row["email"], row["address"], row["city"], row["zipcode"], row["last_activity_date"], row["source"]])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=newsletter.csv"})

def notify_and_remove_waitlist_users(date, time_slot, send_func):
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM waitlist
            WHERE preferred_date = ? AND preferred_time = ?
            ORDER BY created_at
        """, (date, time_slot))
        users = c.fetchall()
        for user in users:
            try:
                send_func(dict(user))
                c.execute("DELETE FROM waitlist WHERE id = ?", (user["id"],))
            except Exception as e:
                import logging
                logging.getLogger("booking").error(f"Failed to notify/remove waitlist user: {e}")
        conn.commit()

@router.get("/protected-data")
@limiter.limit("2/minute")
async def protected_data(request: Request):
    """Example endpoint with rate limiting and dependency injection."""
    return {"data": "protected"}

# Example of logging in an endpoint

@router.get("/log-demo")
def log_demo():
    logger.info("This is an info log from /log-demo endpoint.")
    logger.warning("This is a warning log from /log-demo endpoint.")
    logger.error("This is an error log from /log-demo endpoint.")
    return {"message": "Logging demo complete."}

@router.get("/admin/kpis")
def admin_kpis(user=Depends(admin_required)):
    """
    Returns KPIs: total bookings, bookings this week, bookings this month, waitlist count.
    """
    # Calculate current week and month
    today = datetime.now()
    year, week, _ = today.isocalendar()
    first_of_month = today.replace(day=1)
    # Weekly DB path
    db_path = os.path.join("backend/weekly_databases", f"bookings_{year}-{week:02d}.db")
    # Monthly bookings
    monthly_bookings = []
    # Total bookings (all weekly DBs)
    total_bookings = 0

    # Count bookings for this week
    week_count = 0
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM bookings")
            week_count = c.fetchone()[0]

    # Count bookings for this month (across all weekly DBs)
    for fname in os.listdir("backend/weekly_databases"):
        if fname.endswith(".db"):
            with sqlite3.connect(os.path.join("backend/weekly_databases", fname)) as conn:
                c = conn.cursor()
                c.execute("SELECT date FROM bookings")
                for (date_str,) in c.fetchall():
                    try:
                        d = datetime.strptime(date_str, "%Y-%m-%d")
                        if d >= first_of_month and d.month == today.month and d.year == today.year:
                            monthly_bookings.append(date_str)
                        total_bookings += 1
                    except Exception:
                        continue

    # Waitlist count
    waitlist_count = 0
    waitlist_db = os.path.join("backend", "mh-bookings.db")
    if os.path.exists(waitlist_db):
        with sqlite3.connect(waitlist_db) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM waitlist")
            waitlist_count = c.fetchone()[0]








    }        "waitlist": waitlist_count        "month": len(monthly_bookings),        "week": week_count,        "total": total_bookings,    return {    return {
        "total": total_bookings,
        "week": week_count,
        "month": len(monthly_bookings),
        "waitlist": waitlist_count
    }

