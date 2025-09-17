from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from . import models, schemas

TZ = ZoneInfo("Asia/Taipei")

# Rooms

def get_rooms(db: Session):
    return db.scalars(select(models.Room).order_by(models.Room.id)).all()

def get_room(db: Session, room_id: int):
    return db.get(models.Room, room_id)

def create_room(db: Session, room_in: schemas.RoomCreate):
    room = models.Room(name=room_in.name, description=room_in.description)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def get_rooms_weekly(db: Session):
    now = datetime.now(TZ)
    end = now + timedelta(days=7)
    rooms = db.scalars(select(models.Room).order_by(models.Room.id)).all()
    # Eager load filtered bookings manually (simple approach)
    for r in rooms:
        filtered = []
        for b in r.bookings:
            st = b.start_time
            et = b.end_time
            if st is None or et is None:
                continue
            # Coerce naive datetimes to Asia/Taipei (legacy rows)
            if st.tzinfo is None:
                st = st.replace(tzinfo=TZ)
            else:
                st = st.astimezone(TZ)
            if et.tzinfo is None:
                et = et.replace(tzinfo=TZ)
            else:
                et = et.astimezone(TZ)
            if st < end and et > now:
                # write back normalized (optional)
                b.start_time = st
                b.end_time = et
                filtered.append(b)
    # Sort for stable display
    r.bookings = sorted(filtered, key=lambda x: x.start_time)
    return rooms

def _validate_time_window(category: models.BookingCategory, start: datetime, end: datetime) -> bool:
    # assume incoming datetimes already localized (tz-aware) or naive local; convert to local aware
    if start.tzinfo is None:
        start_local = start.replace(tzinfo=TZ)
    else:
        start_local = start.astimezone(TZ)
    if end.tzinfo is None:
        end_local = end.replace(tzinfo=TZ)
    else:
        end_local = end.astimezone(TZ)
    local_start_hour = start_local.hour
    local_end_hour = end_local.hour
    if category == models.BookingCategory.activity:
        return 5 <= local_start_hour < 22 and 5 < local_end_hour <= 22 and local_end_hour > local_start_hour
    if category == models.BookingCategory.meeting:
        return 5 <= local_start_hour < 17 and 5 < local_end_hour <= 17 and local_end_hour > local_start_hour
    return False

def _is_half_hour(dt: datetime) -> bool:
    return dt.minute in (0,30) and dt.second == 0 and dt.microsecond == 0

# Bookings

def create_booking(db: Session, booking_in: schemas.BookingCreate):
    # validation for category time window and 30-min increments
    start = booking_in.start_time
    end = booking_in.end_time
    # Coerce naive to Asia/Taipei
    if start.tzinfo is None:
        start = start.replace(tzinfo=TZ)
    else:
        start = start.astimezone(TZ)
    if end.tzinfo is None:
        end = end.replace(tzinfo=TZ)
    else:
        end = end.astimezone(TZ)
    if not _is_half_hour(start) or not _is_half_hour(end):
        raise ValueError("時間需為整點或半小時")
    if not _validate_time_window(models.BookingCategory(booking_in.category), start, end):
        raise ValueError("不在允許的時間範圍")
    # conflict detection
    conflict_stmt = select(models.Booking).where(
        models.Booking.room_id == booking_in.room_id,
        models.Booking.status != models.BookingStatus.rejected,
        or_(
            and_(start >= models.Booking.start_time, start < models.Booking.end_time),
            and_(end > models.Booking.start_time, end <= models.Booking.end_time),
            and_(start <= models.Booking.start_time, end >= models.Booking.end_time)
        )
    )
    conflict = db.execute(conflict_stmt).first()
    if conflict:
        return None
    booking = models.Booking(
        room_id=booking_in.room_id,
        user_name=booking_in.user_name,
        user_identity=booking_in.user_identity,
        purpose=booking_in.purpose,
        category=booking_in.category,
        start_time=start,
        end_time=end,
        requested_at=datetime.now(TZ),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def list_bookings(db: Session, room_id: int | None = None, status: models.BookingStatus | None = None):
    stmt = select(models.Booking).order_by(models.Booking.start_time.desc())
    if room_id:
        stmt = stmt.where(models.Booking.room_id == room_id)
    if status:
        stmt = stmt.where(models.Booking.status == status)
    return db.scalars(stmt).all()

def update_booking_status(db: Session, booking_id: int, status: models.BookingStatus):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        return None
    booking.status = status
    db.commit()
    db.refresh(booking)
    return booking

def delete_booking(db: Session, booking_id: int):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        return False
    db.delete(booking)
    db.commit()
    return True

def create_semester_bookings(db: Session, payload: schemas.SemesterBookingCreate):
    created_ids = []
    skipped = []
    # Build first occurrence date that matches weekday >= start_date
    current = payload.start_date
    # advance to weekday
    while current.weekday() != payload.weekday:
        current += timedelta(days=1)
    # iterate weekly
    while current <= payload.end_date:
        hh_s, mm_s = map(int, payload.start_time_hm.split(':'))
        hh_e, mm_e = map(int, payload.end_time_hm.split(':'))
        start_dt = datetime(current.year, current.month, current.day, hh_s, mm_s, tzinfo=TZ)
        end_dt = datetime(current.year, current.month, current.day, hh_e, mm_e, tzinfo=TZ)
        try:
            booking_in = schemas.BookingCreate(
                room_id=payload.room_id,
                user_name=payload.user_name,
                user_identity=payload.user_identity,
                purpose=payload.purpose,
                category=payload.category,
                start_time=start_dt,
                end_time=end_dt,
            )
            b = create_booking(db, booking_in)
            if b:
                created_ids.append(b.id)
            else:
                skipped.append(start_dt.isoformat())
        except ValueError:
            skipped.append(start_dt.isoformat())
        current += timedelta(days=7)
    return created_ids, skipped
