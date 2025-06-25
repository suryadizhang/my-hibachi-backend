import sqlite3
import pytest
from .database import get_db

# test_database.py


def test_get_db_returns_connection():
    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_get_db_row_factory_is_row():
    conn = get_db()
    assert conn.row_factory == sqlite3.Row
    conn.close()

def test_company_newsletter_table_exists():
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(company_newsletter)")
    columns = [row[1] for row in c.fetchall()]
    expected_columns = {
        "id", "name", "phone", "email", "address", "city", "zipcode", "last_activity_date", "source"
    }
    assert set(columns) >= expected_columns
    conn.close()

def test_get_db_returns_new_connection_each_time():
    conn1 = get_db()
    conn2 = get_db()
    assert conn1 is not conn2
    conn1.close()
    conn2.close()import sqlite3
import pytest
from .database import get_db

# test_database.py


def test_get_db_returns_connection():
    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_company_newsletter_table_exists():
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(company_newsletter)")
    columns = [row[1] for row in c.fetchall()]
    expected_columns = {
        "id", "name", "phone", "email", "address", "city", "zipcode", "last_activity_date", "source"
    }
    assert set(columns) >= expected_columns
    conn.close()

def test_get_db_row_factory_is_row():
    conn = get_db()
    assert conn.row_factory == sqlite3.Row
    conn.close()