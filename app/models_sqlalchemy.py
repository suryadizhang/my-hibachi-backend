from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum,
    Index, UniqueConstraint, Boolean, Date, Time
)
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

import enum
class UserRole(enum.Enum):
    admin = "admin"
    staff = "staff"
    user = "user"

class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    email = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    waitlists = relationship("Waitlist", back_populates="user", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_booking_date_time", "date", "time_slot"),
        UniqueConstraint("date", "time_slot", "email", name="uq_booking_slot_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    address = Column(String(255))
    city = Column(String(100))
    zipcode = Column(String(20))
    date = Column(Date, nullable=False, index=True)
    time_slot = Column(Time, nullable=False, index=True)
    contact_preference = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deposit_received = Column(Boolean, default=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    user = relationship("User", back_populates="bookings")

class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, index=True)

    # Changed from String(20) to Date + Time:
    preferred_date = Column(Date, nullable=False, index=True)
    preferred_time = Column(Time, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="waitlists")

class Newsletter(Base):
    __tablename__ = "newsletter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    email = Column(String(255), nullable=False, unique=True, index=True)
    address = Column(String(255))
    city = Column(String(100))
    zipcode = Column(String(20))
    last_activity_date = Column(Date)  # if you want a real date
    source = Column(String(50), nullable=False)        # booking, inquiry, waitlist, etc.
    consent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)