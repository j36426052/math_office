from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import Base, engine, SessionLocal
from backend.app import models
import datetime

client = TestClient(app)

# Ensure fresh DB for test run (sqlite file) - for simplicity drop & create
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Seed rooms manually
with SessionLocal() as db:
    for name in ["116","221","電腦教室","204","研討一","研討二"]:
        db.add(models.Room(name=name))
    db.commit()


def test_create_booking_and_conflict():
    # align to next full hour to satisfy half-hour rule
    base = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = base + datetime.timedelta(hours=1)
    end = start + datetime.timedelta(hours=2)
    payload = {
        "room_id": 1,
        "user_name": "張三",
        "user_identity": "S1234567",
        "purpose": "討論",
    "category": "activity",
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    }
    r = client.post("/bookings", json=payload)
    assert r.status_code == 200, r.text
    booking_id = r.json()["id"]

    # Overlap booking should fail
    payload2 = payload | {"user_name": "李四"}
    r2 = client.post("/bookings", json=payload2)
    assert r2.status_code == 409

    # Non overlapping booking should pass
    start2 = end  # directly after first booking, no overlap
    end2 = start2 + datetime.timedelta(hours=1)
    payload3 = payload | {"start_time": start2.isoformat(), "end_time": end2.isoformat(), "user_name": "王五"}
    r3 = client.post("/bookings", json=payload3)
    assert r3.status_code == 200

    # Approve first booking
    r4 = client.patch(f"/admin/bookings/{booking_id}", json={"status": "approved"})
    assert r4.status_code == 200
    assert r4.json()["status"] == "approved"


def test_list_rooms_and_bookings():
    r = client.get("/rooms")
    assert r.status_code == 200
    rooms = r.json()
    assert len(rooms) >= 1

    r2 = client.get("/bookings")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_rooms_weekly():
    r = client.get("/rooms/weekly")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_semester_booking_creation():
    # pick next Monday for deterministic weekday (weekday=0 => Monday)
    today = datetime.date.today()
    days_ahead = (0 - today.weekday()) % 7
    next_monday = today + datetime.timedelta(days=days_ahead or 7)
    end_range = next_monday + datetime.timedelta(weeks=3)
    payload = {
        "room_id": 1,
        "category": "activity",
        "user_name": "助教A",
        "user_identity": "TA001",
        "purpose": "課程",
        "weekday": 0,
        "start_date": next_monday.isoformat(),
        "end_date": end_range.isoformat(),
        "start_time_hm": "09:00",
        "end_time_hm": "10:00"
    }
    r = client.post('/admin/semester_bookings', json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'created_ids' in data
    assert len(data['created_ids']) >= 3  # at least 3 Mondays in range
    # Re-submit to force conflicts (should skip all)
    r2 = client.post('/admin/semester_bookings', json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2['created_ids']) == 0
    assert len(data2['skipped_conflicts']) >= len(data['created_ids'])
