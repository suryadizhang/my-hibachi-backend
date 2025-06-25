from pydantic import BaseModel, EmailStr
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BookingCreate(BaseModel):
    """Request body for creating a new booking."""
    name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    zipcode: str
    date: str
    time_slot: str
    contact_preference: str

class WaitlistCreate(BaseModel):
    """Request body for joining the waitlist."""
    name: str
    phone: str
    email: EmailStr
    preferred_date: str
    preferred_time: str

class CancelBookingRequest(BaseModel):
    """Request body for cancelling a booking (admin only)."""
    reason: str

class WaitlistEntry(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr
    preferred_date: str
    preferred_time: str
    created_at: str

class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(255), nullable=False)
    hashed_password = sa.Column(sa.String(255), nullable=False)
    # If other string columns exist, also specify length, e.g.:
    # email = sa.Column(sa.String(255), nullable=False)