from apscheduler.schedulers.background import BackgroundScheduler
from .email_utils import send_deposit_reminder, notify_admin_deposit_missing
from .database import get_week_db
import logging
import sqlite3

logger = logging.getLogger("booking")
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_deposit_jobs(booking_id, booking_date):
    # Reminder after 4 hours
    scheduler.add_job(
        func=send_deposit_reminder_job,
        trigger='date',
        run_date=datetime.now() + timedelta(hours=4),
        args=[booking_id, booking_date],
        id=f"reminder_{booking_id}",
        replace_existing=True
    )
    # Admin notification after 6 hours
    scheduler.add_job(
        func=notify_admin_deposit_missing_job,
        trigger='date',
        run_date=datetime.now() + timedelta(hours=6),
        args=[booking_id, booking_date],
        id=f"admin_notify_{booking_id}",
        replace_existing=True
    )

def send_deposit_reminder_job(booking_id, booking_date):
    booking = get_booking_by_id(booking_id, booking_date)
    if booking and not booking.get("deposit_received"):
        send_deposit_reminder(booking)

def notify_admin_deposit_missing_job(booking_id, booking_date):
    booking = get_booking_by_id(booking_id, booking_date)
    if booking and not booking.get("deposit_received"):
        notify_admin_deposit_missing(booking)

def get_booking_by_id(booking_id, booking_date):
    conn = get_week_db(booking_date)
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = c.fetchone()
    return dict(row) if row else None