import pytest
from fastapi.testclient import TestClient
from datetime import date

from app.main import app
from app.database import Base, engine, SessionLocal
from app import models

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


def seed_room(db, name="測試室"):
    r = models.Room(name=name)
    db.add(r); db.commit(); db.refresh(r)
    return r


def test_semester_user_tuesdays_16_weeks_empty_db(client, db):
    room = seed_room(db)
    payload = {
        "room_id": room.id,
        "category": "activity",
        "user_name": "使用者",
        "user_identity": "U",
        "purpose": "",
        "start_time_hm": "08:00",
        "end_time_hm": "10:00",
        "start_date": date(2025,9,2).isoformat(),
        "end_date": date(2025,12,16).isoformat(),
    }
    r = client.post('/admin/semester_bookings', json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data['created_ids']) == 16
    assert len(data['skipped_conflicts']) == 0

    # Re-submit same payload -> expect all skipped as conflicts
    r2 = client.post('/admin/semester_bookings', json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2['created_ids']) == 0
    assert len(data2['skipped_conflicts']) == 16
