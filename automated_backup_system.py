#!/usr/bin/env python3
"""
Automated Database Backup System
Runs daily at 12:00 AM and emails backup to specified email
"""

import os
import sqlite3
import shutil
import smtplib
from datetime import datetime
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import zipfile
import logging
from pathlib import Path

# Email configuration
BACKUP_EMAIL_TO = "suraydizhang.chef@gmail.com"
SMTP_HOST = "smtp.ionos.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "cs@myhibachichef.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "myhibachicustomers!")

# Database paths
DB_PATH = "mh-bookings.db"
BACKUP_DIR = "backups"
LOG_FILE = "backup_system.log"

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_backup():
    """Create a compressed database backup with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mh-bookings-backup-{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Create database backup
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
            
            # Create compressed version
            zip_filename = f"mh-bookings-backup-{timestamp}.zip"
            zip_path = os.path.join(BACKUP_DIR, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, backup_filename)
                
            # Remove uncompressed backup
            os.remove(backup_path)
            
            # Get file size
            file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
            
            logger.info(f"Backup created successfully: {zip_filename} ({file_size:.2f} MB)")
            return zip_path, zip_filename, file_size
        else:
            logger.error(f"Database file not found: {DB_PATH}")
            return None, None, 0
            
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return None, None, 0


def get_database_stats():
    """Get database statistics for the email report"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get table counts
        tables = ['bookings', 'waitlist', 'admins', 'newsletter_recipients']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[table] = "Table not found"
        
        # Get recent bookings (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE date >= date('now', '-7 days')
        """)
        stats['recent_bookings'] = cursor.fetchone()[0]
        
        # Get pending deposits
        cursor.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE deposit_confirmed = 0 OR deposit_confirmed IS NULL
        """)
        stats['pending_deposits'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {}


def send_backup_email(backup_path, backup_filename, file_size):
    """Send backup file via email"""
    try:
        # Get database statistics
        stats = get_database_stats()
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = BACKUP_EMAIL_TO
        msg['Subject'] = f"My Hibachi Database Backup - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Email body
        body = f"""
Daily Database Backup Report
============================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup File: {backup_filename}
File Size: {file_size:.2f} MB

DATABASE STATISTICS:
-------------------
Total Bookings: {stats.get('bookings', 'N/A')}
Waitlist Entries: {stats.get('waitlist', 'N/A')}
Admin Accounts: {stats.get('admins', 'N/A')}
Newsletter Recipients: {stats.get('newsletter_recipients', 'N/A')}

Recent Activity (Last 7 days):
New Bookings: {stats.get('recent_bookings', 'N/A')}
Pending Deposits: {stats.get('pending_deposits', 'N/A')}

BACKUP DETAILS:
--------------
- Database backed up successfully
- Compressed with ZIP compression
- Backup stored locally in: backups/{backup_filename}
- Email delivery: Automated daily at 12:00 AM

NEXT STEPS:
----------
- Download and store backup in secure location
- Verify backup integrity if needed
- Contact support if any issues: info@myhibachichef.com

Best regards,
My Hibachi Chef Backup System

---
This is an automated message from the My Hibachi booking system.
For technical support, contact your system administrator.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach backup file
        with open(backup_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {backup_filename}'
        )
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        text = msg.as_string()
        server.sendmail(SMTP_USER, BACKUP_EMAIL_TO, text)
        server.quit()
        
        logger.info(f"Backup email sent successfully to {BACKUP_EMAIL_TO}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send backup email: {str(e)}")
        return False


def cleanup_old_backups(keep_days=30):
    """Remove backup files older than specified days"""
    try:
        backup_path = Path(BACKUP_DIR)
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        removed_count = 0
        for backup_file in backup_path.glob("mh-bookings-backup-*.zip"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                removed_count += 1
                
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backup files")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {str(e)}")


def main():
    """Main backup process"""
    logger.info("Starting automated database backup process...")
    
    # Create backup
    backup_path, backup_filename, file_size = create_backup()
    
    if backup_path and backup_filename:
        # Send email with backup
        email_sent = send_backup_email(backup_path, backup_filename, file_size)
        
        if email_sent:
            logger.info("Backup process completed successfully")
        else:
            logger.error("Backup created but email failed")
            
        # Cleanup old backups
        cleanup_old_backups()
        
    else:
        logger.error("Backup process failed")
        
        # Send error notification
        try:
            msg = EmailMessage()
            msg['Subject'] = "My Hibachi Database Backup FAILED"
            msg['From'] = SMTP_USER
            msg['To'] = BACKUP_EMAIL_TO
            msg.set_content(f"""
BACKUP FAILURE ALERT
===================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The automated database backup process failed.

Please check the system immediately:
1. Verify database file exists: {DB_PATH}
2. Check system logs: {LOG_FILE}
3. Ensure backup directory is writable: {BACKUP_DIR}

Contact your system administrator if the issue persists.

This is an automated error notification from the My Hibachi backup system.
            """)
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
                
            logger.info("Backup failure notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send failure notification: {str(e)}")


if __name__ == "__main__":
    main()
