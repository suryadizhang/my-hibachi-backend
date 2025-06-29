import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'weekly_databases')
os.makedirs(DB_DIR, exist_ok=True)

def get_week_db(date_str: str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    year, week, _ = date.isocalendar()
    db_path = os.path.join(DB_DIR, f"bookings_{year}-{week:02d}.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Bookings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            zipcode TEXT,
            date TEXT,
            time_slot TEXT,
            contact_preference TEXT,
            created_at TEXT,
            deposit_received INTEGER DEFAULT 0
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_time_slot ON bookings(date, time_slot)")
    # Company Newsletter table
    c.execute("""
        CREATE TABLE IF NOT EXISTS company_newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT NOT NULL UNIQUE,
            address TEXT,
            city TEXT,
            zipcode TEXT,
            last_activity_date TEXT,
            source TEXT
        )
    """)
    conn.commit()
    return conn

def init_user_db():
    db_path = os.path.join(DB_DIR, "users.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('superadmin', 'admin')),
            full_name TEXT,
            email TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_login TEXT,
            is_active INTEGER DEFAULT 1,
            password_reset_required INTEGER DEFAULT 0,
            created_by TEXT
        )
    """)
    
    # Create activity logs for user management
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            target_user TEXT,
            details TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    return conn

def get_user_db():
    db_path = os.path.join(DB_DIR, "users.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

DB_PATH = Path(__file__).parent.parent / "mh-bookings.db"

def get_db():
    conn = sqlite3.connect("mh-bookings.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Ensure company_newsletter table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS company_newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT NOT NULL UNIQUE,
            address TEXT,
            city TEXT,
            zipcode TEXT,
            last_activity_date TEXT,
            source TEXT
        )
    """)
    # Ensure activity_logs table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            description TEXT NOT NULL,
            reason TEXT,
            details TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        # Bookings
        c.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                contact_preference TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deposit_received INTEGER DEFAULT 0
            )
        ''')
        c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_time_slot ON bookings(date, time_slot)")
        # Newsletter
        c.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('superadmin', 'admin')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Waitlist
        c.execute('''
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                preferred_date TEXT NOT NULL,
                preferred_time TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Company Newsletter
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_newsletter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                email TEXT NOT NULL UNIQUE,
                address TEXT,
                city TEXT,
                zipcode TEXT,
                last_activity_date TEXT,
                source TEXT
            )
        ''')
        # Activity Logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                description TEXT NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        # After your table creation, ensure the column exists:
        try:
            c.execute(
                "ALTER TABLE bookings ADD COLUMN deposit_received "
                "INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass  # Column already exists
        c.execute(
            "SELECT * FROM waitlist ORDER BY preferred_date, preferred_time, "
            "created_at"
        )
        conn.commit()


# Ensure the company_newsletter table exists in the main database at startup
conn = sqlite3.connect("mh-bookings.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS company_newsletter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT NOT NULL UNIQUE,
        address TEXT,
        city TEXT,
        zipcode TEXT,
        last_activity_date TEXT,
        source TEXT
    )
""")
conn.commit()
conn.close()

