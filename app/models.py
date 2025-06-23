from pydantic import BaseModel, EmailStr

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