import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.ionos.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "cs@myhibachichef.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "myhibachicustomers!")

def send_email(subject, to, content):
    """Send a plain text email using the configured SMTP server."""
    # Skip email sending during testing
    if os.environ.get("TESTING") == "true" or os.environ.get("DISABLE_EMAIL") == "true":
        print(f"TEST MODE: Would send email to {to} with subject: {subject}")
        return
        
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
        "info@myhibachichef.com",
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
    """Send booking confirmation email to customer AND info@myhibachichef.com."""
    # Skip email sending during testing
    if os.environ.get("TESTING") == "true" or os.environ.get("DISABLE_EMAIL") == "true":
        print(f"TEST MODE: Would send confirmation email to {booking.email} and info@myhibachichef.com")
        return
        
    subject = f"Your Booking Confirmation for {booking.date} at {booking.time_slot}"
    plain_text = f"""Thank you for your booking!

Here are your details:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

To secure your booking, a $100.00 deposit is required within 6 hours.
We look forward to serving you!

Best regards,
My Hibachi Chef Team

For questions, contact us at info@myhibachichef.com
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
    
    # Send to customer
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = booking.email
    msg.set_content(plain_text)
    msg.add_alternative(html_content, subtype='html')
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    
    # Send copy to info@myhibachichef.com
    admin_subject = f"COPY: Booking Confirmation Sent to {booking.name} for {booking.date}"
    admin_content = f"""Booking confirmation has been sent to customer.

Customer Details:
Name: {booking.name}
Email: {booking.email}
Phone: {booking.phone}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

The customer has been notified that a $100 deposit is required within 6 hours.
"""
    send_email(admin_subject, "info@myhibachichef.com", admin_content)

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

def send_deposit_confirmation_email(booking, admin_reason=""):
    """Send deposit confirmation email to customer AND info@myhibachichef.com."""
    if os.environ.get("TESTING") == "true" or os.environ.get("DISABLE_EMAIL") == "true":
        print(f"TEST MODE: Deposit confirmation to {booking.email} and info@myhibachichef.com")
        return
        
    subject = f"Deposit Received - Your Booking is Confirmed for {booking.date}"
    customer_content = f"""Great news! We have received your deposit.

Your booking is now confirmed:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

We look forward to serving you an amazing hibachi experience!

Best regards,
My Hibachi Chef Team

For questions, contact us at info@myhibachichef.com
"""
    
    # Send to customer
    send_email(subject, booking.email, customer_content)
    
    # Send notification to info@myhibachichef.com
    admin_subject = f"DEPOSIT CONFIRMED: {booking.name} - {booking.date} at {booking.time_slot}"
    admin_content = f"""Deposit has been confirmed for booking:

Customer Details:
Name: {booking.name}
Email: {booking.email}
Phone: {booking.phone}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

Admin Reason: {admin_reason if admin_reason else 'Deposit confirmed via admin panel'}

The customer has been notified that their booking is confirmed.
"""
    send_email(admin_subject, "info@myhibachichef.com", admin_content)


def send_booking_cancellation_email(booking, reason=""):
    """Send cancellation confirmation to customer AND info@myhibachichef.com."""
    if os.environ.get("TESTING") == "true" or os.environ.get("DISABLE_EMAIL") == "true":
        print(f"TEST MODE: Cancellation email to {booking.email} and info@myhibachichef.com")
        return
        
    subject = f"Booking Cancellation Confirmation - {booking.date} at {booking.time_slot}"
    customer_content = f"""Your booking has been cancelled.

Cancelled Booking Details:
Name: {booking.name}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

Reason for cancellation: {reason if reason else 'Cancelled upon request'}

If you have any questions or would like to make a new booking, please contact us.

Best regards,
My Hibachi Chef Team

Contact us at info@myhibachichef.com
"""
    
    # Send to customer
    send_email(subject, booking.email, customer_content)
    
    # Send notification to info@myhibachichef.com
    admin_subject = f"BOOKING CANCELLED: {booking.name} - {booking.date} at {booking.time_slot}"
    admin_content = f"""Booking has been cancelled:

Customer Details:
Name: {booking.name}
Email: {booking.email}
Phone: {booking.phone}
Date: {booking.date}
Time Slot: {booking.time_slot}
Address: {booking.address}, {booking.city}, {booking.zipcode}

Cancellation Reason: {reason if reason else 'Cancelled upon request'}

The customer has been notified of the cancellation.
"""
    send_email(admin_subject, "info@myhibachichef.com", admin_content)