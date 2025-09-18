from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List

class BookingStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class BookingCategory(str, Enum):
    activity = "activity"
    meeting = "meeting"
    course = "course"  # 課程

class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    room_id: int
    user_name: str = Field(..., description="申請者姓名")
    user_identity: str = Field(..., description="身份 (學號/教師/其他)")
    purpose: Optional[str] = None
    category: BookingCategory = BookingCategory.activity
    start_time: datetime
    end_time: datetime

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    status: BookingStatus
    created_at: datetime
    requested_at: datetime
    is_semester: bool = False
    class Config:
        from_attributes = True

class BookingWithRoom(Booking):
    room: Room

class BookingUpdateStatus(BaseModel):
    status: BookingStatus

class RoomWithBookings(Room):
    bookings: List[Booking] = []

# Weekly view schema
class WeeklyRoom(Room):
    bookings: List[Booking] = []  # bookings limited to next 7 days

# Semester recurring booking schema
class SemesterBookingCreate(BaseModel):
    room_id: int
    category: BookingCategory = BookingCategory.activity
    user_name: str
    user_identity: str
    purpose: Optional[str] = None
    start_time_hm: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time_hm: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    start_date: date
    end_date: date

class SemesterBookingResult(BaseModel):
    created_ids: List[int]
    skipped_conflicts: List[str]  # ISO start datetimes that were skipped due to conflicts
