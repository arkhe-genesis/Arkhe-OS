from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_coherence():
    response = client.get("/api/coherence")
    assert response.status_code == 200
    assert "phi_c" in response.json()

def test_kym():
    response = client.get("/api/kym/challenge")
    assert response.status_code == 200
    assert "challenge" in response.json()
