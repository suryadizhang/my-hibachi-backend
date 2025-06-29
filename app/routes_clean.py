from fastapi import (
    APIRouter, HTTPException, Depends, BackgroundTasks, Body, Request
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from .database import get_week_db, get_user_db
from .auth import (
    hash_password, verify_password, create_access_token, decode_access_token
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sqlite3
from .email_utils import (
    send_booking_email,
    send_customer_confirmation,
    send_cancellation_email,
    send_waitlist_slot_opened,
    send_waitlist_position_email,
)
from .models import (
    BookingCreate, WaitlistCreate, CancelBookingRequest
)
import logging
from .deposit_tasks import schedule_deposit_jobs
from .utils import (
    upsert_newsletter_entry, notify_all_waitlist_users
)
import csv
from io import StringIO
from slowapi import Limiter
from slowapi.util import get_remote_address

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
        raise HTTPException(
            status_code=403, detail="Superadmin privileges required"
        )
    return user


def admin_required(user=Depends(get_current_user)):
    if user["role"] not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=403, detail="Admin privileges required"
        )
    return user


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_user_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    user = c.fetchone()
    if not user or not verify_password(
        form_data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=401, detail="Incorrect username or password"
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/superadmin/create_admin")
def create_admin(
    username: str, password: str, user=Depends(superadmin_required)
):
    conn = get_user_db()
    c = conn.cursor()
    password_hash = hash_password(password)
    c.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, "admin")
    )
    conn.commit()
    return {"message": f"Admin user '{username}' created successfully"}


@router.post("/book")
@limiter.limit("10/minute")
def book_service(
    data: BookingCreate, background_tasks: BackgroundTasks, request: Request
):
    with get_week_db(data.date) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?",
            (data.date, data.time_slot)
        )
        count = c.fetchone()[0]
    # Comment out debug print for production
    # print(f"DEBUG: Booking count for {data.date} {data.time_slot}: "
    #       f"{count}")
        if count >= 3:
            raise HTTPException(
                status_code=400, detail="This slot is fully booked."
            )
        c.execute("""
            INSERT INTO bookings (name, phone, email, address, city, zipcode,
                                date, time_slot, contact_preference, created_at,
                                deposit_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.name, data.phone, data.email, data.address, data.city,
            data.zipcode, data.date, data.time_slot, data.contact_preference,
            datetime.now(ZoneInfo("America/New_York")).isoformat(), False
        ))
        conn.commit()

    background_tasks.add_task(send_booking_email, data.model_dump())
    background_tasks.add_task(send_customer_confirmation, data)

    schedule_deposit_jobs(data.model_dump())

    # Upsert newsletter entry
    upsert_newsletter_entry(data.model_dump(), "booking")
    return {"message": "Booking created successfully"}


@router.get("/admin/weekly")
def admin_weekly(start_date: str, user=Depends(admin_required)):
    date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    year, week, _ = date_obj.isocalendar()
    db_path = os.path.join(
        "backend/weekly_databases", f"bookings_{year}-{week:02d}.db"
    )

    if not os.path.exists(db_path):
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM bookings ORDER BY date, time_slot, created_at"
        )
        return [dict(row) for row in c.fetchall()]


@router.get("/admin/monthly")
def admin_monthly(year: int, month: int, user=Depends(admin_required)):
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    bookings = []
    for week_num in range(1, 54):  # Cover all possible weeks in a year
        y, w = year, week_num
        db_path = os.path.join(
            "backend/weekly_databases", f"bookings_{y}-{w:02d}.db"
        )
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT * FROM bookings WHERE date BETWEEN ? AND ?
                    ORDER BY date, time_slot, created_at
                """, (first_day.strftime("%Y-%m-%d"),
                      last_day.strftime("%Y-%m-%d")))
                bookings.extend([dict(row) for row in c.fetchall()])
    return bookings


@router.get("/availability")
def get_availability(date: str):
    with get_week_db(date) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT time_slot, COUNT(*) as count FROM bookings
            WHERE date = ? GROUP BY time_slot
        """, (date,))
        booked = {row[0]: row[1] for row in c.fetchall()}

    availability = []
    time_slots = ["11:00 AM", "1:00 PM", "3:00 PM", "5:00 PM", "7:00 PM"]
    for slot in time_slots:
        count = booked.get(slot, 0)
        if count >= 3:
            status = "full"
        elif count >= 2:
            status = "limited"
        else:
            status = "available"
        availability.append({"time_slot": slot, "status": status})
    return availability


@router.post("/waitlist")
@limiter.limit("5/minute")
def join_waitlist(
    data: WaitlistCreate, background_tasks: BackgroundTasks, request: Request
):
    conn = get_user_db()
    c = conn.cursor()
    with conn:
        c.execute("""
            INSERT INTO waitlist (name, phone, email, preferred_date,
                                preferred_time)
            VALUES (?, ?, ?, ?, ?)
        """, (data.name, data.phone, data.email, data.preferred_date,
              data.preferred_time))

    # Get waitlist position
    c.execute("""
        SELECT id FROM waitlist WHERE preferred_date = ? AND preferred_time = ?
        ORDER BY created_at
    """, (data.preferred_date, data.preferred_time))
    ids = [row[0] for row in c.fetchall()]
    position = ids.index(c.lastrowid) + 1 if c.lastrowid in ids else len(ids)

    background_tasks.add_task(
        send_waitlist_position_email, data.dict(), position
    )
    # Upsert newsletter entry
    upsert_newsletter_entry(data.dict(), "waitlist")

    return {"message": f"Added to waitlist. You are number {position} in line."}


@router.delete("/admin/cancel_booking")
def cancel_booking_admin(
    cancel_data: CancelBookingRequest = Body(...),
    user=Depends(admin_required)
):
    """Cancel a booking by ID, send cancellation email, and log the action."""
    booking_id = cancel_data.booking_id
    reason = cancel_data.reason

    # Find the booking across all weekly databases
    booking = None
    db_used = None
    for fname in os.listdir("backend/weekly_databases"):
        if fname.endswith(".db"):
            db_path = os.path.join("backend/weekly_databases", fname)
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
                result = c.fetchone()
                if result:
                    booking = dict(result)
                    db_used = db_path
                    c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
                    conn.commit()
                    break

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    logger.info(
        f"Admin {user['username']} cancelled booking {booking_id} "
        f"for reason: {reason}"
    )

    # Send cancellation email and notify waitlist
    send_cancellation_email(booking, reason)
    notify_all_waitlist_users(
        booking["date"], booking["time_slot"], send_waitlist_slot_opened
    )

    return {"message": "Booking cancelled and customer notified"}


@router.post("/admin/mark_deposit_received")
def mark_deposit_received(
    deposit_data: dict = Body(...), user=Depends(admin_required)
):
    """Mark a booking's deposit as received (admin only)."""
    booking_id = deposit_data.get("booking_id")

    if not booking_id:
        raise HTTPException(
            status_code=400, detail="booking_id is required"
        )

    # Find and update the booking across all weekly databases
    booking_found = False
    for fname in os.listdir("backend/weekly_databases"):
        if fname.endswith(".db"):
            db_path = os.path.join("backend/weekly_databases", fname)
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT * FROM bookings WHERE id = ?", (booking_id,)
                )
                booking = c.fetchone()
                if booking:
                    c.execute(
                        "UPDATE bookings SET deposit_received = ? WHERE id = ?",
                        (True, booking_id)
                    )
                    conn.commit()
                    booking_found = True
                    break

    if not booking_found:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"message": "Deposit marked as received"}


@router.post("/admin/move_waitlist_to_booking")
def move_waitlist_to_booking(
    waitlist_id: int, user=Depends(admin_required)
):
    """Move a waitlist entry to bookings and notify the user (admin only)."""
    conn = get_user_db()
    c = conn.cursor()

    # Get waitlist entry
    c.execute("SELECT * FROM waitlist WHERE id = ?", (waitlist_id,))
    waitlist_entry = c.fetchone()
    if not waitlist_entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    # Convert to booking data
    booking_data = {
        "name": waitlist_entry["name"],
        "phone": waitlist_entry["phone"],
        "email": waitlist_entry["email"],
        "address": "",  # Not available in waitlist
        "city": "",
        "zipcode": "",
        "date": waitlist_entry["preferred_date"],
        "time_slot": waitlist_entry["preferred_time"],
        "contact_preference": "email",
        "created_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
        "deposit_received": False
    }

    # Add to bookings
    with get_week_db(booking_data["date"]) as booking_conn:
        booking_c = booking_conn.cursor()
        booking_c.execute("""
            INSERT INTO bookings (name, phone, email, address, city, zipcode,
                                date, time_slot, contact_preference, created_at,
                                deposit_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_data["name"], booking_data["phone"], booking_data["email"],
            booking_data["address"], booking_data["city"],
            booking_data["zipcode"], booking_data["date"],
            booking_data["time_slot"], booking_data["contact_preference"],
            booking_data["created_at"], booking_data["deposit_received"]
        ))
        booking_conn.commit()

    # Remove from waitlist
    c.execute("DELETE FROM waitlist WHERE id = ?", (waitlist_id,))
    conn.commit()

    # Send booking confirmation email to user
    send_customer_confirmation(type("Booking", (), booking_data))
    # Upsert newsletter entry
    upsert_newsletter_entry(booking_data, "booking")
    return {
        "message": f"Waitlist entry {waitlist_id} moved to bookings "
                  f"and user notified."
    }


@router.get("/admin/newsletter/export")
def export_newsletter(user=Depends(admin_required)):
    """Export all company newsletter contacts as CSV (admin only)."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT name, phone, email, address, city, zipcode,
                   last_activity_date, source FROM company_newsletter
        """)
        rows = c.fetchall()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "name", "phone", "email", "address", "city", "zipcode",
        "last_activity_date", "source"
    ])
    for row in rows:
        writer.writerow([
            row["name"], row["phone"], row["email"], row["address"],
            row["city"], row["zipcode"], row["last_activity_date"],
            row["source"]
        ])
    output.seek(0)
    return StreamingResponse(
        output, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=newsletter.csv"}
    )


@router.get("/admin/newsletter/recipients")
def get_newsletter_recipients(city: str = None, user=Depends(admin_required)):
    """Get all newsletter recipients, optionally filtered by city."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        if city and city.strip():
            query = """SELECT name, phone, email, address, city, zipcode,
                      last_activity_date, source FROM company_newsletter
                      WHERE city LIKE ?"""
            c.execute(query, (f"%{city.strip()}%",))
        else:
            query = """SELECT name, phone, email, address, city, zipcode,
                      last_activity_date, source FROM company_newsletter"""
            c.execute(query)

        rows = c.fetchall()
        recipients = []
        for row in rows:
            recipients.append({
                "name": row["name"],
                "phone": row["phone"],
                "email": row["email"],
                "address": row["address"],
                "city": row["city"],
                "zipcode": row["zipcode"],
                "last_activity_date": row["last_activity_date"],
                "source": row["source"]
            })

    return {
        "recipients": recipients,
        "total_count": len(recipients),
        "filtered_by_city": city if city and city.strip() else None
    }


@router.post("/admin/newsletter/send")
def send_newsletter(
    newsletter_data: dict,
    user=Depends(admin_required)
):
    """Send newsletter to recipients (admin only)."""
    try:
        subject = newsletter_data.get("subject", "My Hibachi Newsletter")
        message = newsletter_data.get("message", "")
        city_filter = newsletter_data.get("city_filter", "")
        send_type = newsletter_data.get("send_type", "email")

        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Newsletter message cannot be empty"
            )

        # For now, only support email sending
        if send_type != "email":
            raise HTTPException(
                status_code=400,
                detail="SMS sending is not yet implemented"
            )

        from .database import get_db
        with get_db() as conn:
            c = conn.cursor()
            if city_filter and city_filter.strip():
                query = """SELECT name, email FROM company_newsletter
                          WHERE city LIKE ? AND email IS NOT NULL
                          AND email != ''"""
                c.execute(query, (f"%{city_filter.strip()}%",))
            else:
                query = """SELECT name, email FROM company_newsletter
                          WHERE email IS NOT NULL AND email != ''"""
                c.execute(query)

            recipients = c.fetchall()

        if not recipients:
            return {
                "success": False,
                "message": "No email recipients found",
                "sent_count": 0,
                "failed_count": 0
            }

        # Mock email sending (replace with actual email service implementation)
        sent_count = 0
        failed_count = 0

        # TODO: Implement actual email sending logic here
        # For now, we'll simulate sending
        for recipient in recipients:
            try:
                # This is where you would integrate with your email service
                # e.g., SendGrid, AWS SES, SMTP, etc.
                print(f"[MOCK EMAIL] To: {recipient['email']} "
                      f"({recipient['name']})")
                print(f"Subject: {subject}")
                print(f"Message: {message}")
                sent_count += 1
            except Exception as e:
                print(f"Failed to send to {recipient['email']}: {e}")
                failed_count += 1

        return {
            "success": True,
            "message": f"Newsletter sent to {sent_count} recipients",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_recipients": len(recipients)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send newsletter: {str(e)}"
        )


@router.get("/admin/newsletter/cities")
def get_newsletter_cities(user=Depends(admin_required)):
    """Get all unique cities from newsletter database (admin only)."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        query = """SELECT DISTINCT city FROM company_newsletter
                  WHERE city IS NOT NULL AND city != '' ORDER BY city"""
        c.execute(query)
        cities = [row["city"] for row in c.fetchall()]

    return {"cities": cities}


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
                logging.getLogger("booking").error(
                    f"Failed to notify/remove waitlist user: {e}"
                )
        conn.commit()


@router.get("/protected-data")
@limiter.limit("2/minute")
async def protected_data(request: Request):
    """Example endpoint with rate limiting and dependency injection."""
    return {"data": "protected"}


@router.get("/log-demo")
def log_demo():
    logger.info("This is an info log from /log-demo endpoint.")
    logger.warning("This is a warning log from /log-demo endpoint.")
    logger.error("This is an error log from /log-demo endpoint.")
    return {"message": "Logging demo complete."}


@router.get("/admin/kpis")
def admin_kpis(user=Depends(admin_required)):
    """
    Returns KPIs: total bookings, bookings this week,
    bookings this month, waitlist count.
    """
    # Calculate current week and month
    today = datetime.now()
    year, week, _ = today.isocalendar()
    first_of_month = today.replace(day=1)
    # Weekly DB path
    db_path = os.path.join(
        "backend/weekly_databases", f"bookings_{year}-{week:02d}.db"
    )
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
            with sqlite3.connect(
                os.path.join("backend/weekly_databases", fname)
            ) as conn:
                c = conn.cursor()
                c.execute("SELECT date FROM bookings")
                for (date_str,) in c.fetchall():
                    try:
                        d = datetime.strptime(date_str, "%Y-%m-%d")
                        if (d >= first_of_month and d.month == today.month
                                and d.year == today.year):
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

    return {
        "total": total_bookings,
        "week": week_count,
        "month": len(monthly_bookings),
        "waitlist": waitlist_count
    }
