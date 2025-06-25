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
    subject = f"Your Booking Confirmation for {booking.date} at {booking.time_slot}"
    to = booking.email
    plain_text = f"""Thank you for your booking!

Here are your details:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

To secure your booking, a $100.00 deposit is required within 6 hours.
We look forward to serving you!
"""
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; padding: 24px;">
          <h2 style="color: #E94F37;">My Hibachi Chef – Booking Confirmation</h2>
          <p>Thank you for your booking!</p>
          <ul>
            <li><strong>Name:</strong> {booking.name}</li>
            <li><strong>Date:</strong> {booking.date}</li>
            <li><strong>Time Slot:</strong> {booking.time_slot}</li>
            <li><strong>Address:</strong> {booking.address}, {booking.city}, {booking.zipcode}</li>
          </ul>
          <p style="color:#b71c1c;"><strong>To secure your booking, a $100 deposit is required within 6 hours.</strong></p>
          <p>We look forward to serving you!<br/>— My Hibachi Chef Team</p>
          <hr/>
          <p style="font-size: 12px; color: #888;">For questions, contact us at <a href="mailto:info@myhibachichef.com">info@myhibachichef.com</a></p>
        </div>
      </body>
    </html>
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to
    msg.set_content(plain_text)
    msg.add_alternative(html_content, subtype='html')
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

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

def notify_admin_deposit_missing(booking): notify_admin_deposit_missing(booking):
    """Notify admin if deposit has not been received after 6 hours."""""Notify admin if deposit has not been received after 6 hours."""
    send_email(    send_email(
        f"Deposit Not Received for Booking {booking.name} on {booking.date} at {booking.time_slot}", {booking.name} on {booking.date} at {booking.time_slot}",
        "info@myhibachichef.com",
        f"""The following booking has not received a deposit after 6 hours: following booking has not received a deposit after 6 hours:

Name: {booking.name}
Email: {booking.email}
Date: {booking.date}Date: {booking.date}
Time Slot: {booking.time_slot}time_slot}

Please follow up with the customer or consider cancelling the booking.h the customer or consider cancelling the booking.
"""
    )    )

def send_waitlist_slot_opened(waitlist_user): send_waitlist_slot_opened(waitlist_user):
    """Notify a waitlist user that a slot has opened up."""""Notify a waitlist user that a slot has opened up."""
    send_email(    send_email(
        f"Good News! A Slot Has Opened Up for {waitlist_user['preferred_date']} at {waitlist_user['preferred_time']}", {waitlist_user['preferred_date']} at {waitlist_user['preferred_time']}",
        waitlist_user['email'],
        f"""Hello {waitlist_user['name']},lo {waitlist_user['name']},

A slot has just opened up for your requested date and time:our requested date and time:
Date: {waitlist_user['preferred_date']}
Time Slot: {waitlist_user['preferred_time']}Time Slot: {waitlist_user['preferred_time']}

Please reply to this email or contact us as soon as possible if you would like to claim this slot.s as soon as possible if you would like to claim this slot.

Best regards,Best regards,
My Hibachi Chef Team
""""""
    )