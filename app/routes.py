from fastapi import (
    APIRouter, HTTPException, Depends, BackgroundTasks, Body, Request, Form
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from .database import get_week_db, get_user_db
from .auth import (
    hash_password, verify_password, create_access_token, decode_access_token
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List
import os
import sqlite3
from .email_utils import (
    send_booking_email,
    send_customer_confirmation,
    send_waitlist_confirmation,
    send_waitlist_slot_opened,
    send_waitlist_position_email,
    send_deposit_confirmation_email,
    send_booking_cancellation_email,
)
from .models import (
    BookingCreate, WaitlistCreate, CancelBookingRequest, WaitlistEntry
)
import logging
from .deposit_tasks import schedule_deposit_jobs
from .utils import (
    get_latest_user_info, upsert_newsletter_entry, notify_all_waitlist_users
)
from .websocket_manager import websocket_manager
import csv
from io import StringIO
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    
    username = payload["sub"]
    
    # First check users table
    conn = get_user_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user:
        return user
    
    # Then check admins table in main database
    with sqlite3.connect("mh-bookings.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        if admin:
            # Convert admin to user-like format for compatibility
            return {
                "id": admin["id"],
                "username": admin["username"],
                "role": admin["user_type"],
                "password_hash": admin["password_hash"]
            }
    
    # Check admins table in users database
    conn = get_user_db()
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE username = ?", (username,))
    admin = c.fetchone()
    if admin:
        # Convert admin to user-like format for compatibility
        return {
            "id": admin["id"],
            "username": admin["username"],
            "role": admin["user_type"],
            "password_hash": admin["password_hash"]
        }
    
    raise HTTPException(status_code=401, detail="User not found")

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

@router.post("/admin/login")
def admin_login(credentials: dict):
    """Authenticate admin user and return a JWT access token."""
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password required"
        )
    
    # First check users table (where superadmin creates new admins)
    conn = get_user_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1 AND role IN ('admin', 'superadmin')",
        (username,)
    )
    user = c.fetchone()
    
    if user and verify_password(password, user["password_hash"]):
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": user["role"]
        }
    
    # Then check in main database (mh-bookings.db) for legacy admins
    with sqlite3.connect("mh-bookings.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM admins WHERE username = ? AND is_active = 1",
            (username,)
        )
        admin = cursor.fetchone()
        
        if admin and verify_password(password, admin["password_hash"]):
            access_token = create_access_token(
                data={"sub": admin["username"], "role": admin["user_type"]}
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_type": admin["user_type"]
            }
    
    raise HTTPException(status_code=401, detail="Invalid admin credentials")



@router.post("/superadmin/create_admin")
def create_admin(
    username: str = Form(...), 
    password: str = Form(...),
    user=Depends(superadmin_required)
):
    """Create a new admin user (superadmin only)."""
    conn = get_user_db()
    c = conn.cursor()
    try:
        current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
        c.execute("""
            INSERT INTO users (username, password_hash, role, full_name, 
                             email, created_at, updated_at, is_active, 
                             password_reset_required, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, hash_password(password), "admin", username.title(),
            f"{username}@myhibachi.com", current_time, current_time, 1, 0,
            user["username"]
        ))
        conn.commit()

        # Log the action
        c.execute("""
            INSERT INTO user_activity_logs (user_id, action, target_user, 
                                          details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user["id"], "create_admin", username,
            f"Created admin account: {username}", current_time
        ))
        conn.commit()

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": f"Admin '{username}' created successfully"}

@router.get("/superadmin/admins")
def list_admins(user=Depends(superadmin_required)):
    """List all admin users (superadmin only)."""
    conn = get_user_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, full_name, email, created_at, updated_at, 
               last_login, is_active, password_reset_required, created_by
        FROM users 
        WHERE role = 'admin' 
        ORDER BY created_at DESC
    """)
    admins = [dict(row) for row in c.fetchall()]
    return {"admins": admins}

@router.delete("/superadmin/admin/{admin_username}")
def delete_admin(admin_username: str, user=Depends(superadmin_required)):
    """Delete an admin user (superadmin only)."""
    if admin_username == user["username"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    conn = get_user_db()
    c = conn.cursor()
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (admin_username,))
    admin = c.fetchone()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Delete the admin
    c.execute("DELETE FROM users WHERE username = ? AND role = 'admin'", (admin_username,))
    
    # Log the action
    current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    c.execute("""
        INSERT INTO user_activity_logs (user_id, action, target_user, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user["id"], "delete_admin", admin_username, 
        f"Deleted admin account: {admin_username}", current_time
    ))
    conn.commit()
    
    return {"message": f"Admin '{admin_username}' deleted successfully"}

@router.post("/superadmin/admin/{admin_username}/reset_password")
def reset_admin_password(admin_username: str, new_password: str = None, user=Depends(superadmin_required)):
    """Reset an admin's password (superadmin only). If no password provided, uses default."""
    default_passwords = {
        "karen": "myhibachicustomers!",
        "yohan": "gedeinbiji"
    }
    
    # Use provided password or default
    password = new_password if new_password else default_passwords.get(admin_username, "defaultpassword123!")
    
    conn = get_user_db()
    c = conn.cursor()
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (admin_username,))
    admin = c.fetchone()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Update password
    current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    c.execute("""
        UPDATE users 
        SET password_hash = ?, updated_at = ?, password_reset_required = 1
        WHERE username = ? AND role = 'admin'
    """, (hash_password(password), current_time, admin_username))
    
    # Log the action
    c.execute("""
        INSERT INTO user_activity_logs (user_id, action, target_user, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user["id"], "reset_password", admin_username, 
        f"Reset password for admin: {admin_username}", current_time
    ))
    conn.commit()
    
    return {"message": f"Password reset for admin '{admin_username}'", "new_password": password}

@router.put("/superadmin/admin/{admin_username}")
def update_admin(admin_username: str, full_name: str = None, email: str = None, 
                is_active: bool = None, user=Depends(superadmin_required)):
    """Update admin account details (superadmin only)."""
    conn = get_user_db()
    c = conn.cursor()
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (admin_username,))
    admin = c.fetchone()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Build update query
    updates = []
    params = []
    
    if full_name is not None:
        updates.append("full_name = ?")
        params.append(full_name)
    
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    updates.append("updated_at = ?")
    params.append(current_time)
    params.append(admin_username)
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE username = ? AND role = 'admin'"
    c.execute(query, params)
    
    # Log the action
    details = f"Updated admin {admin_username}: " + ", ".join([
        f"{field}={value}" for field, value in [
            ("full_name", full_name), ("email", email), ("is_active", is_active)
        ] if value is not None
    ])
    
    c.execute("""
        INSERT INTO user_activity_logs (user_id, action, target_user, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user["id"], "update_admin", admin_username, details, current_time
    ))
    conn.commit()
    
    return {"message": f"Admin '{admin_username}' updated successfully"}

@router.get("/superadmin/activity_logs")
def get_admin_activity_logs(limit: int = 100, user=Depends(superadmin_required)):
    """Get admin activity logs (superadmin only)."""
    conn = get_user_db()
    c = conn.cursor()
    c.execute("""
        SELECT ual.*, u.username as actor_username
        FROM user_activity_logs ual
        LEFT JOIN users u ON ual.user_id = u.id
        ORDER BY ual.timestamp DESC
        LIMIT ?
    """, (limit,))
    logs = [dict(row) for row in c.fetchall()]
    return {"logs": logs}

@router.post("/admin/change_password")
def change_own_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user=Depends(admin_required)
):
    """Allow admin to change their own password."""
    # Verify current password
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(
            status_code=400, 
            detail="Current password is incorrect"
        )

    conn = get_user_db()
    c = conn.cursor()

    current_time = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat()
    c.execute("""
        UPDATE users
        SET password_hash = ?, updated_at = ?, password_reset_required = 0
        WHERE id = ?
    """, (hash_password(new_password), current_time, user["id"]))

    # Log the action
    c.execute("""
        INSERT INTO user_activity_logs 
        (user_id, action, target_user, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user["id"], "change_password", user["username"],
        "Changed own password", current_time
    ))
    conn.commit()

    return {"message": "Password changed successfully"}

@router.post("/book")
@limiter.limit("5/minute")
async def book_service(data: BookingCreate, background_tasks: BackgroundTasks, request: Request):
    """Create a new booking and send confirmation emails."""
    logger.info(f"Received booking request: {data.model_dump()}")
    
    conn = get_week_db(data.date)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?", (data.date, data.time_slot))
    count = c.fetchone()[0]
    logger.info(f"Booking count for {data.date} {data.time_slot}: {count}")
    if count >= 2:
        raise HTTPException(status_code=400, detail="This slot is fully booked.")
    
    # Insert the booking
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
    
    # Calculate new status after booking
    new_count = count + 1
    if new_count == 1:
        new_status = "waiting"
    elif new_count >= 2:
        new_status = "booked"
    else:
        new_status = "available"
    
    # Send real-time WebSocket notification
    try:
        await websocket_manager.notify_availability_change(
            data.date, 
            data.time_slot, 
            new_status
        )
        logger.info(f"WebSocket notification sent for {data.date} {data.time_slot}: {new_status}")
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")
    
    # Background tasks
    background_tasks.add_task(send_booking_email, data)
    background_tasks.add_task(send_customer_confirmation, data)
    schedule_deposit_jobs(booking_id, data.date)
    # Upsert newsletter entry
    upsert_newsletter_entry(data.model_dump(), "booking")
    return {"message": "Booking successful", "booking_id": booking_id}

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

# Phase 1: Bulk availability endpoint for enhanced caching
@router.post("/availability/bulk")
async def get_bulk_availability(dates: List[str]):
    """Get availability status for multiple dates at once - Phase 1 improvement"""
    try:
        result = {}
        
        for date in dates:
            try:
                conn = get_week_db(date)
                c = conn.cursor()
                c.execute(
                    "SELECT time_slot, COUNT(*) as count FROM bookings WHERE date = ? GROUP BY time_slot",
                    (date,)
                )
                slots = {row["time_slot"]: row["count"] for row in c.fetchall()}
                all_slots = ['12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM']
                
                date_result = {}
                for slot in all_slots:
                    count = slots.get(slot, 0)
                    if count == 0:
                        status = "available"
                    elif count == 1:
                        status = "waiting"
                    else:
                        status = "booked"
                    date_result[slot] = {"status": status}
                
                result[date] = date_result
                
            except Exception as e:
                logger.warning(f"Error fetching availability for {date}: {e}")
                # Return default available status on error
                result[date] = {
                    slot: {"status": "available"} for slot in ['12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM']
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Bulk availability error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching bulk availability")


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
async def cancel_booking(
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
                    # Check count before deletion for WebSocket notification
                    c.execute("SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?", 
                             (booking["date"], booking["time_slot"]))
                    count_before = c.fetchone()[0]
                    
                    c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
                    conn.commit()
                    found = True
                    cancelled_booking = dict(booking)
                    logger.info(f"Admin {user['username']} cancelled booking {booking_id} for reason: {reason}")
                    
                    # Calculate new status after cancellation
                    new_count = count_before - 1
                    if new_count == 0:
                        new_status = "available"
                    elif new_count == 1:
                        new_status = "waiting"
                    else:
                        new_status = "booked"
                    
                    # Send real-time WebSocket notification
                    try:
                        await websocket_manager.notify_availability_change(
                            booking["date"], 
                            booking["time_slot"], 
                            new_status
                        )
                        logger.info(f"WebSocket notification sent for cancellation {booking['date']} {booking['time_slot']}: {new_status}")
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket notification: {e}")
                    
                    try:
                        # Create a booking object for the new email function
                        booking_obj = type("Booking", (), {
                            "name": cancelled_booking['name'],
                            "email": cancelled_booking['email'],
                            "phone": cancelled_booking['phone'],
                            "date": cancelled_booking['date'],
                            "time_slot": cancelled_booking['time_slot'],
                            "address": cancelled_booking['address'],
                            "city": cancelled_booking['city'],
                            "zipcode": cancelled_booking['zipcode']
                        })()
                        
                        send_booking_cancellation_email(booking_obj, reason)
                    except Exception as e:
                        logger.error(f"Failed to send cancellation email: {e}")
                    # Notify the first user on the waitlist for this slot
                    notify_all_waitlist_users(booking["date"], booking["time_slot"], send_waitlist_slot_opened)
                    break
    if not found:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking cancelled", "booking": cancelled_booking}

@router.post("/admin/confirm_deposit")
def confirm_deposit(
    booking_id: int,
    date: str,
    reason: str = Body(..., embed=True),
    user=Depends(admin_required)
):
    """Admin marks a booking as deposit received and sends notification."""
    from .utils import log_activity
    
    conn = get_week_db(date)
    c = conn.cursor()
    
    # Get booking details first
    c.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = c.fetchone()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking_dict = dict(booking)
    
    # Update deposit status
    c.execute(
        "UPDATE bookings SET deposit_received = 1 WHERE id = ?",
        (booking_id,)
    )
    conn.commit()
    
    # Log the activity
    log_activity(
        username=user["username"],
        action_type="DEPOSIT_CONFIRMED",
        entity_type="BOOKING",
        entity_id=booking_id,
        description=f"Confirmed deposit received for booking {booking_id} "
                    f"({booking_dict['name']} - {booking_dict['date']} "
                    f"{booking_dict['time_slot']})",
        reason=reason,
        details=f"Date: {date}, Customer: {booking_dict['name']}, "
                f"Email: {booking_dict['email']}"
    )
    
    # Send email notification to customer and info@myhibachichef.com
    try:
        # Create a booking object for the email function
        booking_obj = type("Booking", (), {
            "name": booking_dict['name'],
            "email": booking_dict['email'],
            "phone": booking_dict['phone'],
            "date": booking_dict['date'],
            "time_slot": booking_dict['time_slot'],
            "address": booking_dict['address'],
            "city": booking_dict['city'],
            "zipcode": booking_dict['zipcode']
        })()
        
        send_deposit_confirmation_email(booking_obj, reason)
        
        logger.info(
            f"Deposit confirmation emails sent for booking {booking_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to send deposit confirmation email: {e}")
        # Don't fail the whole operation if email fails
    
    # Optionally: Remove scheduled jobs for this booking
    try:
        from .deposit_tasks import scheduler
        scheduler.remove_job(f"reminder_{booking_id}")
        scheduler.remove_job(f"admin_notify_{booking_id}")
    except Exception as e:
        logger.warning(f"Failed to remove scheduled jobs: {e}")
    
    return {"message": "Deposit confirmed and notification sent"}


@router.post("/admin/create-sample-data")
def create_sample_data(user=Depends(admin_required)):
    """Create sample test data for development and testing."""
    from .utils import log_activity
    import subprocess
    import sys
    
    try:
        # Run the sample data creation script
        script_path = os.path.join(
            os.path.dirname(__file__), '..', 'create_sample_db.py'
        )
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            # Log the activity
            log_activity(
                username=user["username"],
                action_type="DATA_EXPORT",
                entity_type="DATABASE",
                entity_id=None,
                description="Sample test data created successfully",
                reason="Development and testing purposes",
                details="Created fake bookings, newsletters, waitlist, logs"
            )
            
            return {
                "success": True,
                "message": "Sample data created successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "Failed to create sample data",
                "error": result.stderr
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating sample data: {str(e)}"
        }


@router.get("/admin/activity-logs")
def get_activity_logs(
    page: int = 1,
    limit: int = 50,
    entity_type: str = None,
    action_type: str = None,
    user=Depends(admin_required)
):
    """Get activity logs with pagination and filtering."""
    from .database import get_db
    
    offset = (page - 1) * limit
    where_conditions = []
    params = []
    
    if entity_type:
        where_conditions.append("entity_type = ?")
        params.append(entity_type)
    
    if action_type:
        where_conditions.append("action_type = ?")
        params.append(action_type)
    
    where_clause = (" WHERE " + " AND ".join(where_conditions)
                    if where_conditions else "")
    
    with get_db() as conn:
        c = conn.cursor()
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM activity_logs{where_clause}"
        c.execute(count_query, params)
        total = c.fetchone()[0]
        
        # Get logs with pagination
        query = f"""
            SELECT * FROM activity_logs{where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        c.execute(query, params)
        logs = [dict(row) for row in c.fetchall()]
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/admin/waitlist", response_model=list[WaitlistEntry])
def get_waitlist(user=Depends(admin_required)):
    """
    Get all waitlist entries, sorted by preferred_date, preferred_time, and created_at (admin only).
    """
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, name, phone, email, preferred_date, preferred_time, 
                   COALESCE(created_at, datetime('now')) as created_at 
            FROM waitlist 
            ORDER BY preferred_date, preferred_time, created_at
        """)
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
async def move_waitlist_to_booking(waitlist_id: int, user=Depends(admin_required)):
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
        
        # Check current booking count
        c.execute(
            "SELECT COUNT(*) FROM bookings WHERE date = ? AND time_slot = ?",
            (entry["preferred_date"], entry["preferred_time"])
        )
        current_count = c.fetchone()[0]
        if current_count >= 2:
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
        
        # Calculate new status after waitlist move
        new_count = current_count + 1
        if new_count == 1:
            new_status = "waiting"
        elif new_count >= 2:
            new_status = "booked"
        else:
            new_status = "available"
        
        # Send real-time WebSocket notification
        try:
            await websocket_manager.notify_availability_change(
                booking_data["date"], 
                booking_data["time_slot"], 
                new_status
            )
            logger.info(f"WebSocket notification sent for waitlist move {booking_data['date']} {booking_data['time_slot']}: {new_status}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
    
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
    try:
        # Calculate current week and month
        today = datetime.now()
        year, week, _ = today.isocalendar()
        
        # Weekly DB path - use same path as monthly endpoint
        db_path = os.path.join("backend/weekly_databases", f"bookings_{year}-{week:02d}.db")
        
        # Total bookings (all weekly DBs)
        total_bookings = 0

        # Count bookings for this week
        week_count = 0
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM bookings")
                week_count = c.fetchone()[0]

        # Count bookings for this month using the same logic as monthly endpoint
        from calendar import monthrange
        from datetime import date as dt_date
        
        first_day = dt_date(today.year, today.month, 1)
        last_day = dt_date(today.year, today.month, monthrange(today.year, today.month)[1])
        
        # Find all weeks that overlap with this month
        week_files = set()
        day = first_day
        while day <= last_day:
            y, w, _ = day.isocalendar()
            week_files.add((y, w))
            day += timedelta(days=1)
        
        monthly_bookings = []
        for y, w in week_files:
            db_file_path = os.path.join("backend/weekly_databases", f"bookings_{y}-{w:02d}.db")
            if os.path.exists(db_file_path):
                with sqlite3.connect(db_file_path) as conn:
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    c.execute("SELECT * FROM bookings WHERE date BETWEEN ? AND ? ORDER BY date, time_slot, created_at",
                              (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))
                    monthly_bookings.extend([dict(row) for row in c.fetchall()])

        # Count total bookings (all weekly DBs)
        try:
            weekly_db_dir = "backend/weekly_databases"
            if os.path.exists(weekly_db_dir):
                for fname in os.listdir(weekly_db_dir):
                    if fname.endswith(".db") and "bookings_" in fname:
                        full_path = os.path.join(weekly_db_dir, fname)
                        with sqlite3.connect(full_path) as conn:
                            c = conn.cursor()
                            # Check if bookings table exists
                            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
                            if c.fetchone():
                                c.execute("SELECT COUNT(*) FROM bookings")
                                total_bookings += c.fetchone()[0]
        except Exception as e:
            # Log the error but continue
            print(f"Error reading weekly databases: {e}")

        # Waitlist count
        waitlist_count = 0
        waitlist_db = "mh-bookings.db"
        if os.path.exists(waitlist_db):
            with sqlite3.connect(waitlist_db) as conn:
                c = conn.cursor()
                # Check if waitlist table exists
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='waitlist'")
                if c.fetchone():
                    c.execute("SELECT COUNT(*) FROM waitlist")
                    waitlist_count = c.fetchone()[0]

        return {
            "total": total_bookings,
            "week": week_count,
            "month": len(monthly_bookings),
            "waitlist": waitlist_count
        }
    except Exception as e:
        print(f"Error in admin_kpis: {e}")
        raise HTTPException(status_code=500, detail=f"KPI calculation error: {str(e)}")


@router.get("/admin/newsletter/recipients")
def get_newsletter_recipients(
    city: str = "", name: str = "", user=Depends(admin_required)
):
    """Get all newsletter recipients, optionally filtered by city and name."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        
        query_parts = ["SELECT name, phone, email, address, city, zipcode,"]
        query_parts.append("last_activity_date, source")
        query_parts.append("FROM company_newsletter")
        
        conditions = []
        params = []
        
        if city and city.strip():
            conditions.append("city LIKE ?")
            params.append(f"%{city.strip()}%")
            
        if name and name.strip():
            conditions.append("name LIKE ?")
            params.append(f"%{name.strip()}%")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
            
        query = " ".join(query_parts)
        c.execute(query, params)

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
        "filtered_by_city": city if city and city.strip() else None,
        "filtered_by_name": name if name and name.strip() else None
    }


@router.post("/admin/newsletter/send")
def send_newsletter(
    newsletter_data: dict,
    user=Depends(admin_required)
):
    """Send newsletter to recipients (admin only)."""
    from .utils import log_activity
    
    try:
        subject = newsletter_data.get("subject", "My Hibachi Newsletter")
        message = newsletter_data.get("message", "")
        city_filter = newsletter_data.get("city_filter", "")
        send_type = newsletter_data.get("send_type", "email")  # email or sms
        
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
            # Log the attempt even if no recipients
            log_activity(
                    f"Message length: {len(message)} chars"
        )
        
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

@router.get("/admin/all-bookings")
def admin_all_bookings(user=Depends(admin_required)):
    """Get all bookings from all time periods (admin only)."""
    bookings = []
    weekly_db_dir = "backend/weekly_databases"
    
    if os.path.exists(weekly_db_dir):
        for fname in os.listdir(weekly_db_dir):
            if fname.endswith('.db') and 'bookings_' in fname:
                db_path = os.path.join(weekly_db_dir, fname)
                try:
                    with sqlite3.connect(db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        c = conn.cursor()
                        # Check if bookings table exists
                        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
                        if c.fetchone():
                            c.execute("SELECT * FROM bookings ORDER BY date, time_slot, created_at")
                            bookings.extend([dict(row) for row in c.fetchall()])
                except Exception as e:
                    print(f"Error reading {db_path}: {e}")
                    continue
    
    return bookings


# Phase 1: WebSocket endpoint is registered in main.py directly
# This avoids conflicts with the router prefix

