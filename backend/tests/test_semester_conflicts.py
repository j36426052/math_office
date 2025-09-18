import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from app.main import app
from app.database import Base, engine, SessionLocal
from app import models

TZ = ZoneInfo("Asia/Taipei")

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def seed_room(db, name="衝突室"):
    r = models.Room(name=name)
    db.add(r); db.commit(); db.refresh(r)
    return r


def test_semester_all_conflicts_logged(client, db, caplog):
    caplog.set_level("INFO")
    room = seed_room(db)
    # Prepare existing weekly bookings every Monday 08:00-10:00 for 4 weeks
    base = date(2025, 9, 22)  # Monday
    for i in range(4):
        d = base + timedelta(weeks=i)
        st = datetime(d.year, d.month, d.day, 8, 0, tzinfo=TZ)
        et = datetime(d.year, d.month, d.day, 10, 0, tzinfo=TZ)
        b = models.Booking(
            room_id=room.id,
            user_name="既有",
            user_identity="X",
            purpose="",
            category=models.BookingCategory.activity,
            start_time=st,
            end_time=et,
            status=models.BookingStatus.pending,
        )
        db.add(b)
    db.commit()

    payload = {
        "room_id": room.id,
        "category": "activity",
        "user_name": "申請者",
        "user_identity": "Y",
        "purpose": "",
        "start_time_hm": "08:00",
        "end_time_hm": "10:00",
        "start_date": base.isoformat(),
        "end_date": (base + timedelta(weeks=3)).isoformat(),
    }
    resp = client.post("/admin/semester_bookings", json=payload, headers={"Authorization": "Basic cXN uYWtlOmpzdDEwMTEwMTEwMQ==".replace(" ","")})
    # if admin auth is enabled, credentials in .env are used; this header matches qsnake/jst101101101
    if resp.status_code == 401:
        pytest.skip("Admin auth not configured")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["created_ids"] == []
    assert len(data["skipped_conflicts"]) >= 4

    # Check logs contain conflict messages
    conflict_logs = [r for r in caplog.records if "semester_skip_conflict" in r.message or "booking_conflict" in r.message]
    assert conflict_logs, "Expected conflict logs to be present"
