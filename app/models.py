from pydantic import BaseModel, EmailStr

class BookingCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr
    address: str
    date: str  # Format: YYYY-MM-DD
    timeSlot: str
    contactPreference: str

class Booking(BookingCreate):
    id: int
    created_at: str

class BookingOut(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr
    address: str
    date: str
    time_slot: str
    contact_preference: str
    created_at: str