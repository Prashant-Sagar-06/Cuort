import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_register_and_login_flow():
    email = "agent.smith@cuort.ai"
    password = "SuperSecretPassword123"

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Agent Smith",
        "role": "support_agent"
    })
    assert reg_res.status_code in [201, 400]  # 400 if already created in previous run

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "support_agent"

    # 3. Authenticated /me
    token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

def test_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={
        "email": "test@cuort.ai",
        "password": "wrong_password"
    })
    assert res.status_code == 401
