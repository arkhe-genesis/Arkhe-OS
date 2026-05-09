import pytest
import uuid
from datetime import datetime, timezone, timezone
from fastapi.testclient import TestClient
from jose import jwt
from arkhe_core.api.main import app, SECRET_KEY, ALGORITHM

client = TestClient(app)

def create_test_token(game_id: str):
    payload = {
        "game_id": game_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc).timestamp() + 3600
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def test_gameplay_event_unauthorized():
    payload = {"game_id": "test", "player_id": "test", "action": "scan", "target": {}}
    response = client.post("/api/v1/gameplay/event", json=payload)
    # HTTPBearer with auto_error=True (default) returns 403,
    # but depending on Starlette/FastAPI version and if it is not provided at all, it might be 401.
    assert response.status_code in [401, 403]

def test_gameplay_event_authorized_hit():
    game_id = "minecraft-sre"
    token = create_test_token(game_id)
    payload = {
        "game_id": game_id,
        "player_id": "deadbeef12345678",
        "action": "scan",
        "target": {
            "type": "coordinate",
            "data": {"x": 10, "y": 64, "z": 10, "world": "overworld"}
        }
    }
    response = client.post(
        "/api/v1/gameplay/event",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "confirmed"

def test_websocket_stream_auth():
    token = create_test_token("unity-demo")
    with client.websocket_connect(f"/api/v1/stream?token={token}") as websocket:
        websocket.send_text("ping")

def test_websocket_stream_no_auth():
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/stream") as websocket:
            pass
