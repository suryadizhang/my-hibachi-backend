#!/usr/bin/env python3
"""
Debug the monthly KPI calculation discrepancy
"""
import sqlite3
import os
from datetime import datetime

def debug_monthly_kpi():
    print("=== DEBUGGING MONTHLY KPI CALCULATION ===\n")
    
    today = datetime.now()
    year = today.year
    month = today.month
    first_of_month = today.replace(day=1)
    
    print(f"Current date: {today}")
    print(f"First of month: {first_of_month}")
    print(f"Year: {year}, Month: {month}")
    
    # Check what the monthly endpoint does
    print("\n--- MONTHLY ENDPOINT LOGIC ---")
    from calendar import monthrange
    from datetime import date as dt_date, timedelta
    
    first_day = dt_date(year, month, 1)
    last_day = dt_date(year, month, monthrange(year, month)[1])
    print(f"Date range: {first_day} to {last_day}")
    
    week_files = set()
    day = first_day
    while day <= last_day:
        y, w, _ = day.isocalendar()
        week_files.add((y, w))
        day += timedelta(days=1)
    
    print(f"Week files to check: {week_files}")
    
    monthly_bookings = []
    for y, w in week_files:
        db_path = os.path.join("backend/weekly_databases", f"bookings_{y}-{w:02d}.db")
        print(f"Checking: {db_path} (exists: {os.path.exists(db_path)})")
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM bookings WHERE date BETWEEN ? AND ? ORDER BY date, time_slot, created_at",
                          (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))
                week_bookings = [dict(row) for row in c.fetchall()]
                print(f"  Found {len(week_bookings)} bookings")
                for booking in week_bookings:
                    print(f"    Date: {booking['date']}, Time: {booking['time_slot']}")
                monthly_bookings.extend(week_bookings)
    
    print(f"\nMonthly endpoint total: {len(monthly_bookings)} bookings")
    
    # Check what the KPI calculation does
    print("\n--- KPI ENDPOINT LOGIC ---")
    kpi_monthly_bookings = []
    total_bookings = 0
    
    weekly_db_dir = "backend/weekly_databases"
    if os.path.exists(weekly_db_dir):
        for fname in os.listdir(weekly_db_dir):
            if fname.endswith(".db") and "bookings_" in fname:
                full_path = os.path.join(weekly_db_dir, fname)
                print(f"Checking KPI file: {full_path}")
                with sqlite3.connect(full_path) as conn:
                    c = conn.cursor()
                    # Check if bookings table exists
                    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
                    if c.fetchone():
                        c.execute("SELECT date FROM bookings")
                        dates = c.fetchall()
                        print(f"  Found dates: {[d[0] for d in dates]}")
                        for (date_str,) in dates:
                            try:
                                d = datetime.strptime(date_str, "%Y-%m-%d")
                                print(f"    Date {date_str}: d >= first_of_month: {d >= first_of_month}, same month: {d.month == today.month}, same year: {d.year == today.year}")
                                if d >= first_of_month and d.month == today.month and d.year == today.year:
                                    kpi_monthly_bookings.append(date_str)
                                    print(f"      -> COUNTED for this month")
                                total_bookings += 1
                            except Exception as e:
                                print(f"      -> ERROR parsing date: {e}")
                                continue
    
    print(f"\nKPI calculation total: {len(kpi_monthly_bookings)} bookings")
    print(f"KPI monthly bookings: {kpi_monthly_bookings}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Monthly endpoint: {len(monthly_bookings)} bookings")
    print(f"KPI calculation: {len(kpi_monthly_bookings)} bookings")
    if len(monthly_bookings) != len(kpi_monthly_bookings):
        print("❌ MISMATCH FOUND!")
    else:
        print("✅ Counts match!")

if __name__ == "__main__":
    debug_monthly_kpi()
