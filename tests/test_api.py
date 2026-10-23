import os
os.environ["DATABASE_URL"] = "sqlite:///./test_marketflow.db"
os.environ["API_KEY"] = "test-key"
from fastapi.testclient import TestClient
from marketflow.api import app

client = TestClient(app)

from marketflow.db import init_db
init_db()

def test_health(): assert client.get("/health").json()["status"] == "ok"
def test_auth_required(): assert client.post("/v1/events", json={"events":[]}).status_code == 401
def test_validation_and_idempotency():
    event = {"event_id":"test-event-unique", "symbol":"NIFTY", "event_time":"2025-01-01T10:00:00+00:00", "received_time":"2025-01-01T10:00:01+00:00", "price":"100.2", "quantity":"3", "venue":"SIM", "source":"test"}
    first = client.post("/v1/events", headers={"X-API-Key":"test-key"}, json={"events":[event]})
    second = client.post("/v1/events", headers={"X-API-Key":"test-key"}, json={"events":[event]})
    assert first.status_code == 200 and first.json()["accepted"] == 1
    assert second.status_code == 200 and second.json()["duplicates"] == 1
    replay = client.post("/v1/replay", headers={"X-API-Key":"test-key"}, json={"symbol":"NIFTY"})
    assert replay.status_code == 200 and replay.json()["count"] >= 1
