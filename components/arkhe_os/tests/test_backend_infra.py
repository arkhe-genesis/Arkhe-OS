import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arkhe_os.api.main import app
from arkhe_os.db.session import Base, get_db
from arkhe_os.auth.security import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def test_signup(client):
    response = client.post(
        "/v1/auth/signup",
        json={"email": "test@arkhe.io", "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@arkhe.io"

def test_login(client):
    response = client.post(
        "/v1/auth/login",
        data={"username": "test@arkhe.io", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_qe_evaluate_protected(client):
    # Login to get token
    login_resp = client.post(
        "/v1/auth/login",
        data={"username": "test@arkhe.io", "password": "password123"}
    )
    token = login_resp.json()["access_token"]

    # Test protected endpoint
    response = client.post(
        "/v1/evaluate",
        json={
            "action_id": "test-action",
            "description": "Test action for infrastructure optimization",
            "dimensions": {
                "coherence_impact": 0.9,
                "autonomy_preservation": 0.8,
                "learning_capacity": 0.8,
                "decoherence_resilience": 0.8,
                "geometric_beauty": 0.8
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "resonance_score" in response.json()

def test_graphql_state(client):
    query = """
    query {
      getArkheState {
        coherenceM
        phasePhi
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    assert "getArkheState" in response.json()["data"]
