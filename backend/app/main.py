from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, Base, get_db
from sqlalchemy import text
from datetime import datetime
import logging

app = FastAPI(title="教室借用系統 API", docs_url=None, redoc_url=None)

# Basic logging setup for app-specific logs (printed to stdout)
_app_logger = logging.getLogger("math_office")
if not _app_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    _app_logger.addHandler(_handler)
_app_logger.setLevel(logging.INFO)

# -------------------- ADMIN BASIC AUTH --------------------
security = HTTPBasic(auto_error=False)
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

def require_admin(credentials: HTTPBasicCredentials | None = Depends(security)):
    # If credentials not configured -> open (for dev)
    if not ADMIN_USER or not ADMIN_PASS:
        return True
    if not credentials or not credentials.username or not credentials.password:
        # Return 403 to avoid browser basic-auth pop-up (no WWW-Authenticate)
        raise HTTPException(status_code=403, detail="Forbidden")
    user_ok = secrets.compare_digest(credentials.username, ADMIN_USER)
    pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=403, detail="Forbidden")
    return True

# -------------------- CORS CONFIG --------------------
# Environment variables:
# BACKEND_CORS_ALLOW_ALL=true              -> allow all (credentials disabled)
# BACKEND_CORS_ORIGINS=http://a,http://b   -> explicit list
# BACKEND_CORS_ORIGINS_REGEX=^https://.*$  -> regex mode (mutually exclusive with list)
# PUBLIC_HOST=booking.example.edu          -> auto append http/https variants if not present
allow_all_env = os.getenv("BACKEND_CORS_ALLOW_ALL", "false").lower() == "true"
raw_origins = os.getenv("BACKEND_CORS_ORIGINS")
raw_regex = os.getenv("BACKEND_CORS_ORIGINS_REGEX")
public_host = os.getenv("PUBLIC_HOST")

origins: list[str] = []
allow_origin_regex = None
if allow_all_env:
    origins = ["*"]
elif raw_origins:
    origins = [o.strip() for o in raw_origins.split(',') if o.strip() and o.strip() != "*"]
elif raw_regex:
    allow_origin_regex = raw_regex
else:
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

if public_host and not allow_origin_regex and "*" not in origins:
    for proto in ("http", "https"):
        candidate = f"{proto}://{public_host}"
        if candidate not in origins:
            origins.append(candidate)

cors_common = dict(allow_methods=["*"], allow_headers=["*"], expose_headers=["*"], max_age=86400)
if origins == ["*"]:
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, **cors_common)
elif allow_origin_regex:
    app.add_middleware(CORSMiddleware, allow_origin_regex=allow_origin_regex, allow_credentials=True, **cors_common)
else:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, **cors_common)
# -----------------------------------------------------

# Create tables
Base.metadata.create_all(bind=engine)

# Seed rooms if empty
@app.on_event("startup")
async def seed_rooms():
    with next(get_db()) as db:
        # Ensure is_semester column exists for Booking (simple runtime migration for SQLite)
        try:
            cols = [r[1] for r in db.execute(text("PRAGMA table_info(bookings)")).fetchall()]
            if 'is_semester' not in cols:
                db.execute(text("ALTER TABLE bookings ADD COLUMN is_semester BOOLEAN NOT NULL DEFAULT 0"))
                db.commit()
        except Exception:
            pass
        # Initial seed if empty
        if not db.query(models.Room).first():
            initial_rooms = [
                ("志希 116", None),
                ("志希 221（E 化教室）", None),
                ("志希樓電腦教室", None),
                ("大智 204", None),
                ("研討一", None),
                ("研討二", None),
            ]
            for name, desc in initial_rooms:
                db.add(models.Room(name=name, description=desc))
            db.commit()
        else:
            # Migration: rename legacy names and remove old description
            changed = False
            mapping = {
                "116": "志希 116",
                "221": "志希 221（E 化教室）",
                "電腦教室": "志希樓電腦教室",
                "204": "大智 204",
            }
            q = db.query(models.Room).all()
            for r in q:
                if r.name in mapping and r.name != mapping[r.name]:
                    r.name = mapping[r.name]
                    changed = True
                if r.name == "志希樓電腦教室" and r.description:
                    r.description = None
                    changed = True
            if changed:
                db.commit()

@app.get("/rooms/weekly", response_model=list[schemas.WeeklyRoom])
def list_rooms_weekly(db: Session = Depends(get_db)):
    return crud.get_rooms_weekly(db)

@app.get("/rooms", response_model=list[schemas.Room])
def list_rooms(db: Session = Depends(get_db)):
    return crud.get_rooms(db)

@app.get("/rooms/{room_id}", response_model=schemas.RoomWithBookings)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.post("/bookings", response_model=schemas.Booking)
def create_booking(booking_in: schemas.BookingCreate, db: Session = Depends(get_db)):
    if booking_in.end_time <= booking_in.start_time:
        raise HTTPException(status_code=400, detail="結束時間必須晚於開始時間")
    try:
        booking = crud.create_booking(db, booking_in)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    if not booking:
        raise HTTPException(status_code=409, detail="時間衝突，請選擇其他時段")
    return booking

@app.get("/bookings", response_model=list[schemas.Booking])
def list_all_bookings(room_id: int | None = None, status: schemas.BookingStatus | None = None, is_semester: bool | None = None, db: Session = Depends(get_db)):
    return crud.list_bookings(db, room_id=room_id, status=status, is_semester=is_semester)

@app.patch("/admin/bookings/{booking_id}", response_model=schemas.Booking, dependencies=[Depends(require_admin)])
def update_status(booking_id: int, update: schemas.BookingUpdateStatus, db: Session = Depends(get_db)):
    booking = crud.update_booking_status(db, booking_id, update.status)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.delete("/admin/bookings/{booking_id}", dependencies=[Depends(require_admin)])
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_booking(db, booking_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True}

@app.post("/admin/semester_bookings", response_model=schemas.SemesterBookingResult, dependencies=[Depends(require_admin)])
def create_semester(sem_req: schemas.SemesterBookingCreate, db: Session = Depends(get_db)):
    created_ids, skipped = crud.create_semester_bookings(db, sem_req)
    return schemas.SemesterBookingResult(created_ids=created_ids, skipped_conflicts=skipped)

@app.get("/admin/ping", dependencies=[Depends(require_admin)])
def admin_ping():
    # auth_enabled True when ADMIN_USER & ADMIN_PASS both set
    return {"ok": True, "auth_enabled": bool(ADMIN_USER and ADMIN_PASS)}

@app.get("/healthz")
def healthz():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
