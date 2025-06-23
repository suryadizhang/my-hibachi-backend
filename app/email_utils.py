import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.ionos.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

def send_email(subject, to, content):
    """Send a plain text email using the configured SMTP server."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to
    msg.set_content(content)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def send_booking_email(booking):
    """Send a notification email to the admin for a new booking."""
    send_email(
        f"New Booking: {booking.name} on {booking.date} at {booking.time_slot}",
        "book@myhibachichef.com",
        f"""New booking received:

Name: {booking.name}
Phone: {booking.phone}
Email: {booking.email}
Address: {booking.address}
City: {booking.city}
Zipcode: {booking.zipcode}
Date: {booking.date}
Time Slot: {booking.time_slot}
Contact Preference: {booking.contact_preference}
"""
    )

def send_customer_confirmation(booking):
    """Send a booking confirmation email to the customer, including deposit instructions."""
    send_email(
        f"Your Booking Confirmation for {booking.date} at {booking.time_slot}",
        booking.email,
        f"""Thank you for your booking!

Here are your details:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

To secure and lock your booking, a $100.00 deposit is required.
Please complete your deposit within 6 hours of receiving this email, or your booking may be cancelled.

We look forward to serving you!
"""
    )

def send_waitlist_confirmation(waitlist):
    """Send a waitlist confirmation email to the customer."""
    send_email(
        f"Waitlist Confirmation for {waitlist['preferred_date']} at {waitlist['preferred_time']}",
        waitlist['email'],
        f"""Thank you for joining the waitlist!

Here are your details:
Name: {waitlist['name']}
Date: {waitlist['preferred_date']}
Time Slot: {waitlist['preferred_time']}

We will contact you if a slot becomes available.
"""
    )

def send_waitlist_position_email(waitlist, position):
    """Send an email to the user with their waitlist position."""
    send_email(
        f"Waitlist Confirmation: You are #{position} in line",
        waitlist['email'],
        f"""Thank you for joining the waitlist!

Here are your details:
Name: {waitlist['name']}
Date: {waitlist['preferred_date']}
Time Slot: {waitlist['preferred_time']}

You are currently number {position} on the waitlist for this slot.
We will notify you if an opening becomes available.

Best regards,
My Hibachi Chef Team
"""
    )

def send_cancellation_email(booking, reason):
    """Send a booking cancellation email to the customer, including the reason."""
    send_email(
        f"Booking Cancelled for {booking['date']} at {booking['time_slot']}",
        booking['email'],
        f"""Your booking has been cancelled.

Details:
Name: {booking['name']}
Date: {booking['date']}
Time Slot: {booking['time_slot']}

Reason for cancellation: {reason}

If you have questions, please contact us.
"""
    )

def send_deposit_reminder(booking):
    """Send a deposit reminder email to the customer after 4 hours."""
    send_email(
        f"Deposit Reminder for Your Booking on {booking.date} at {booking.time_slot}",
        booking.email,
        f"""This is a reminder that a $100.00 deposit is required to secure your booking.

Please complete your deposit as soon as possible to avoid cancellation.

Booking details:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}

Thank you!
"""
    )

def notify_admin_deposit_missing(booking):
    """Notify admin if deposit has not been received after 6 hours."""
    send_email(
        f"Deposit Not Received for Booking {booking.name} on {booking.date} at {booking.time_slot}",
        "info@myhibachichef.com",
        f"""The following booking has not received a deposit after 6 hours:

Name: {booking.name}
Email: {booking.email}
Date: {booking.date}
Time Slot: {booking.time_slot}

Please follow up with the customer or consider cancelling the booking.
"""
    )

def send_waitlist_slot_opened(waitlist_user):
    """Notify a waitlist user that a slot has opened up."""
    send_email(
        f"Good News! A Slot Has Opened Up for {waitlist_user['preferred_date']} at {waitlist_user['preferred_time']}",
        waitlist_user['email'],
        f"""Hello {waitlist_user['name']},

A slot has just opened up for your requested date and time:
Date: {waitlist_user['preferred_date']}
Time Slot: {waitlist_user['preferred_time']}

Please reply to this email or contact us as soon as possible if you would like to claim this slot.

Best regards,
My Hibachi Chef Team
"""
    )