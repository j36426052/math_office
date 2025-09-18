import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.main import app
from app.database import Base, engine, SessionLocal
from app import models

TZ = ZoneInfo("Asia/Taipei")

@pytest.fixture(autouse=True)
def setup_db():
    # Recreate tables fresh each test run
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def client():
    return TestClient(app)


def create_room(session, name):
    r = models.Room(name=name)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def create_booking(session, room_id, start, end, status=models.BookingStatus.pending):
    b = models.Booking(
        room_id=room_id,
        user_name="User",
        user_identity="ID",
        purpose="Test",
        category=models.BookingCategory.activity,
        start_time=start,
        end_time=end,
        status=status,
    )
    session.add(b)
    session.commit()
    session.refresh(b)
    return b


def test_weekly_rooms_includes_all_rooms_even_without_bookings(client, db):
    r1 = create_room(db, "研討一")
    r2 = create_room(db, "研討二")
    resp = client.get("/rooms/weekly")
    assert resp.status_code == 200
    data = resp.json()
    names = {r["name"] for r in data}
    assert {"研討一", "研討二"}.issubset(names)


def test_weekly_rooms_filters_to_next_7_days(client, db):
    room = create_room(db, "測試室")
    now = datetime.now(TZ)
    # booking within window
    create_booking(db, room.id, now + timedelta(hours=1), now + timedelta(hours=2))
    # booking starting after 8 days (excluded)
    create_booking(db, room.id, now + timedelta(days=8), now + timedelta(days=8, hours=1))
    resp = client.get("/rooms/weekly")
    assert resp.status_code == 200
    data = resp.json()
    target = next(r for r in data if r["name"] == "測試室")
    assert len(target["bookings"]) == 1
    st_iso = target["bookings"][0]["start_time"]
    assert "T" in st_iso


def test_weekly_rooms_excludes_past_only(client, db):
    room = create_room(db, "過去室")
    now = datetime.now(TZ)
    # booking ended yesterday -> should be excluded
    create_booking(db, room.id, now - timedelta(days=1, hours=3), now - timedelta(days=1, hours=1))
    resp = client.get("/rooms/weekly")
    assert resp.status_code == 200
    data = resp.json()
    target = next(r for r in data if r["name"] == "過去室")
    assert target["bookings"] == []


def test_weekly_rooms_includes_crossing_now(client, db):
    room = create_room(db, "跨越室")
    now = datetime.now(TZ)
    # booking started in past but ends in future -> included
    create_booking(db, room.id, now - timedelta(hours=1), now + timedelta(hours=2))
    resp = client.get("/rooms/weekly")
    assert resp.status_code == 200
    data = resp.json()
    target = next(r for r in data if r["name"] == "跨越室")
    assert len(target["bookings"]) == 1
