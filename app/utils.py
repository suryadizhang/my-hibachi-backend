import os
import sqlite3
from datetime import datetime

def get_latest_user_info(email):
    """Fetch the latest address, city, zipcode, and contact_preference for a user from previous bookings."""
    address, city, zipcode, contact_preference = "", "", "", ""
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'weekly_databases')
    for db_file in os.listdir(db_dir):
        if db_file.endswith(".db"):
            db_path = os.path.join(db_dir, db_file)
            with sqlite3.connect(db_path) as bconn:
                bconn.row_factory = sqlite3.Row
                bc = bconn.cursor()
                bc.execute("SELECT * FROM bookings WHERE email = ? ORDER BY created_at DESC LIMIT 1", (email,))
                prev = bc.fetchone()
                if prev:
                    address = prev["address"]
                    city = prev["city"]
                    zipcode = prev["zipcode"]
                    contact_preference = prev["contact_preference"]
                    break
    return address, city, zipcode, contact_preference

def upsert_newsletter_entry(data, source):
    """Insert or update a contact in the company newsletter table."""
    from .database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO company_newsletter (name, phone, email, address, city, zipcode, last_activity_date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                address=excluded.address,
                city=excluded.city,
                zipcode=excluded.zipcode,
                last_activity_date=excluded.last_activity_date,
                source=excluded.source
        """, (
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", ""),
            data.get("city", ""),
            data.get("zipcode", ""),
            datetime.now().strftime("%Y-%m-%d"),
            source
        ))
        conn.commit()

def notify_all_waitlist_users(date, time_slot, send_func):
    """Notify all users on the waitlist for a given slot."""
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
            except Exception as e:
                import logging
                logging.getLogger("booking").error(f"Failed to notify waitlist user: {e}")