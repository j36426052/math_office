from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, Base, get_db
from datetime import datetime

app = FastAPI(title="教室借用系統 API", docs_url=None, redoc_url=None)

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Seed rooms if empty
@app.on_event("startup")
async def seed_rooms():
    with next(get_db()) as db:
        if not db.query(models.Room).first():
            initial_rooms = [
                ("116", None),
                ("221", None),
                ("電腦教室", "電腦設備齊全"),
                ("204", None),
                ("研討一", None),
                ("研討二", None),
            ]
            for name, desc in initial_rooms:
                db.add(models.Room(name=name, description=desc))
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
def list_all_bookings(room_id: int | None = None, status: schemas.BookingStatus | None = None, db: Session = Depends(get_db)):
    return crud.list_bookings(db, room_id=room_id, status=status)

# Admin (simple placeholder, no auth yet)
@app.patch("/admin/bookings/{booking_id}", response_model=schemas.Booking)
def update_status(booking_id: int, update: schemas.BookingUpdateStatus, db: Session = Depends(get_db)):
    booking = crud.update_booking_status(db, booking_id, update.status)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.delete("/admin/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_booking(db, booking_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True}

@app.post("/admin/semester_bookings", response_model=schemas.SemesterBookingResult)
def create_semester(sem_req: schemas.SemesterBookingCreate, db: Session = Depends(get_db)):
    created_ids, skipped = crud.create_semester_bookings(db, sem_req)
    return schemas.SemesterBookingResult(created_ids=created_ids, skipped_conflicts=skipped)
