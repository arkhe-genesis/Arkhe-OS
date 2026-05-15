from fastapi.testclient import TestClient
from src.service import app

client = TestClient(app)

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

def test_metrics():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
