#!/usr/bin/env python3
"""
Database maintenance and backup script
Run weekly via cron job
"""
import os
import sqlite3
import shutil
from datetime import datetime, timedelta
import zipfile

def backup_databases():
    """Create timestamped backups of all databases"""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup main database
    if os.path.exists("mh-bookings.db"):
        shutil.copy2("mh-bookings.db", f"{backup_dir}/mh-bookings_{timestamp}.db")
        print(f"✅ Backed up main database: mh-bookings_{timestamp}.db")
    
    # Backup weekly databases
    weekly_backup_dir = f"{backup_dir}/weekly_{timestamp}"
    if os.path.exists("backend/weekly_databases"):
        shutil.copytree("backend/weekly_databases", weekly_backup_dir)
        print(f"✅ Backed up weekly databases: weekly_{timestamp}/")
    
    # Create compressed archive
    with zipfile.ZipFile(f"{backup_dir}/complete_backup_{timestamp}.zip", 'w') as zipf:
        if os.path.exists(f"{backup_dir}/mh-bookings_{timestamp}.db"):
            zipf.write(f"{backup_dir}/mh-bookings_{timestamp}.db")
        if os.path.exists(weekly_backup_dir):
            for root, dirs, files in os.walk(weekly_backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, backup_dir))
    
    print(f"📦 Complete backup archive: complete_backup_{timestamp}.zip")

def cleanup_old_weekly_dbs():
    """Archive weekly databases older than 6 months"""
    cutoff_date = datetime.now() - timedelta(days=180)
    weekly_dir = "backend/weekly_databases"
    archive_dir = "archived_weekly_dbs"
    
    if not os.path.exists(weekly_dir):
        print("ℹ️ No weekly databases directory found")
        return
    
    os.makedirs(archive_dir, exist_ok=True)
    archived_count = 0
    
    for filename in os.listdir(weekly_dir):
        if filename.endswith('.db'):
            file_path = os.path.join(weekly_dir, filename)
            file_date = datetime.fromtimestamp(os.path.getctime(file_path))
            
            if file_date < cutoff_date:
                shutil.move(file_path, os.path.join(archive_dir, filename))
                archived_count += 1
                print(f"📦 Archived: {filename}")
    
    if archived_count == 0:
        print("ℹ️ No old databases to archive")
    else:
        print(f"✅ Archived {archived_count} old weekly databases")

def cleanup_old_backups():
    """Remove backup files older than 30 days"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        return
    
    cutoff_date = datetime.now() - timedelta(days=30)
    removed_count = 0
    
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            file_date = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_date < cutoff_date:
                os.remove(file_path)
                removed_count += 1
                print(f"🗑️ Removed old backup: {filename}")
    
    if removed_count == 0:
        print("ℹ️ No old backups to remove")
    else:
        print(f"✅ Removed {removed_count} old backup files")

def check_database_integrity():
    """Check integrity of all databases"""
    print("\n🔍 Checking database integrity...")
    
    # Check main database
    if os.path.exists("mh-bookings.db"):
        try:
            conn = sqlite3.connect("mh-bookings.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            if result == "ok":
                print("✅ Main database integrity: OK")
            else:
                print(f"❌ Main database integrity issue: {result}")
            conn.close()
        except Exception as e:
            print(f"❌ Error checking main database: {e}")
    
    # Check weekly databases
    weekly_dir = "backend/weekly_databases"
    if os.path.exists(weekly_dir):
        db_count = 0
        error_count = 0
        for filename in os.listdir(weekly_dir):
            if filename.endswith('.db'):
                db_count += 1
                try:
                    conn = sqlite3.connect(os.path.join(weekly_dir, filename))
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()[0]
                    if result != "ok":
                        print(f"❌ {filename} integrity issue: {result}")
                        error_count += 1
                    conn.close()
                except Exception as e:
                    print(f"❌ Error checking {filename}: {e}")
                    error_count += 1
        
        if error_count == 0:
            print(f"✅ All {db_count} weekly databases integrity: OK")
        else:
            print(f"❌ {error_count}/{db_count} weekly databases have issues")

def generate_database_report():
    """Generate a report of database statistics"""
    print("\n📊 Database Statistics Report")
    print("=" * 50)
    
    # Main database stats
    if os.path.exists("mh-bookings.db"):
        conn = sqlite3.connect("mh-bookings.db")
        cursor = conn.cursor()
        
        # Waitlist count
        cursor.execute("SELECT COUNT(*) FROM waitlist")
        waitlist_count = cursor.fetchone()[0]
        print(f"Waitlist entries: {waitlist_count}")
        
        # Admin count
        cursor.execute("SELECT COUNT(*) FROM admins WHERE is_active = 1")
        admin_count = cursor.fetchone()[0]
        print(f"Active admins: {admin_count}")
        
        conn.close()
    
    # Weekly databases stats
    weekly_dir = "backend/weekly_databases"
    if os.path.exists(weekly_dir):
        total_bookings = 0
        db_count = 0
        
        for filename in os.listdir(weekly_dir):
            if filename.endswith('.db'):
                db_count += 1
                try:
                    conn = sqlite3.connect(os.path.join(weekly_dir, filename))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM bookings")
                    count = cursor.fetchone()[0]
                    total_bookings += count
                    conn.close()
                except:
                    pass
        
        print(f"Total bookings across {db_count} weekly databases: {total_bookings}")
    
    print("=" * 50)

if __name__ == "__main__":
    print("🔧 Starting database maintenance...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    backup_databases()
    cleanup_old_weekly_dbs()
    cleanup_old_backups()
    check_database_integrity()
    generate_database_report()
    
    print("\n✅ Database maintenance completed!")
