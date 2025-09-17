import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

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
    s = SessionLocal();
    try:
        yield s
    finally:
        s.close()


def create_room(db):
    r = models.Room(name='T-101')
    db.add(r)
    db.commit(); db.refresh(r)
    return r


def test_half_hour_within_hour_allowed(client, db):
    room = create_room(db)
    now = datetime.now(TZ).replace(hour=13, minute=0, second=0, microsecond=0)
    payload = {
        'room_id': room.id,
        'user_name': 'u',
        'user_identity': 'i',
        'purpose': 'p',
        'category': 'activity',
        'start_time': (now).isoformat(),
        'end_time': (now + timedelta(minutes=30)).isoformat()
    }
    resp = client.post('/bookings', json=payload)
    assert resp.status_code == 200, resp.text


def test_invalid_end_before_start(client, db):
    room = create_room(db)
    now = datetime.now(TZ).replace(hour=13, minute=0, second=0, microsecond=0)
    payload = {
        'room_id': room.id,
        'user_name': 'u',
        'user_identity': 'i',
        'purpose': 'p',
        'category': 'activity',
        'start_time': (now).isoformat(),
        'end_time': (now - timedelta(minutes=30)).isoformat()
    }
    resp = client.post('/bookings', json=payload)
    assert resp.status_code == 400


def test_outside_window_activity(client, db):
    room = create_room(db)
    base = datetime.now(TZ).replace(hour=4, minute=0, second=0, microsecond=0)
    payload = {
        'room_id': room.id,
        'user_name': 'u',
        'user_identity': 'i',
        'purpose': 'p',
        'category': 'activity',
        'start_time': base.isoformat(),
        'end_time': (base + timedelta(hours=1)).isoformat()
    }
    resp = client.post('/bookings', json=payload)
    assert resp.status_code == 400
