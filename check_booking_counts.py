#!/usr/bin/env python3
import sqlite3
import os

print('=== backend/weekly_databases ===')
db_dir = 'backend/weekly_databases'
total_backend = 0
if os.path.exists(db_dir):
    for fname in os.listdir(db_dir):
        if fname.endswith('.db') and 'bookings_' in fname:
            full_path = os.path.join(db_dir, fname)
            with sqlite3.connect(full_path) as conn:
                c = conn.cursor()
                c.execute('SELECT name FROM sqlite_master WHERE type=? AND name=?', ('table', 'bookings'))
                if c.fetchone():
                    c.execute('SELECT COUNT(*) FROM bookings')
                    count = c.fetchone()[0]
                    total_backend += count
                    print(f'{fname}: {count} bookings')

print(f'\n=== weekly_databases ===')
db_dir = 'weekly_databases'
total_root = 0
if os.path.exists(db_dir):
    for fname in os.listdir(db_dir):
        if fname.endswith('.db') and 'bookings_' in fname:
            full_path = os.path.join(db_dir, fname)
            with sqlite3.connect(full_path) as conn:
                c = conn.cursor()
                c.execute('SELECT name FROM sqlite_master WHERE type=? AND name=?', ('table', 'bookings'))
                if c.fetchone():
                    c.execute('SELECT COUNT(*) FROM bookings')
                    count = c.fetchone()[0]
                    total_root += count
                    print(f'{fname}: {count} bookings')

print(f'\nTotal in backend/weekly_databases: {total_backend}')
print(f'Total in weekly_databases: {total_root}')
