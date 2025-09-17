from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from zoneinfo import ZoneInfo
import enum
from .database import Base

class BookingStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class BookingCategory(str, enum.Enum):
    activity = "activity"  # 05:00-22:00
    meeting = "meeting"    # 05:00-17:00

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    bookings = relationship("Booking", back_populates="room", cascade="all,delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_name = Column(String, nullable=False)
    user_identity = Column(String, nullable=False)  # 學號/職稱等
    purpose = Column(String, nullable=True)
    category = Column(Enum(BookingCategory), nullable=False, default=BookingCategory.activity, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Taipei")), nullable=False)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Taipei")), nullable=False)  # 申請送出時間 (排序用)

    room = relationship("Room", back_populates="bookings")
