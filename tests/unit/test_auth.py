import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.auth.routes import router
from src.backend.auth.service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from src.backend.auth.models import RegisterRequest, LoginRequest, RefreshRequest
from src.backend.db import SessionLocal
from src.backend.shared_models import TeamModel, UserModel

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    # Auth is DB-backed (writes via the global get_db → sentinel_test.db).
    # Clear users + teams before each test so reused emails don't collide.
    db = SessionLocal()
    try:
        db.query(UserModel).delete()
        db.query(TeamModel).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_register_success():
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"
    assert data["user"]["is_active"] is True


def test_register_duplicate_email():
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "anotherpassword123",
            "name": "Another User",
            "team_name": "Another Team",
        },
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_short_password():
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "short",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    assert response.status_code == 422


def test_login_success():
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_invalid_credentials():
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword123",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_refresh_token_success():
    register_response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    refresh_token_value = register_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token_value},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"


def test_refresh_token_invalid():
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


def test_refresh_token_wrong_type():
    import jwt

    token = jwt.encode(
        {"sub": "user123", "type": "access", "team_id": "team123", "role": "admin"},
        "test-refresh-secret-key",
        algorithm="HS256",
    )
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] is not None  # token type validation


def test_me_success():
    register_response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    access_token = register_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["is_active"] is True


def test_me_unauthorized():
    response = client.get("/auth/me")
    assert response.status_code in [401, 403]


def test_me_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_me_expired_token():
    import jwt
    from datetime import datetime, timedelta, timezone

    user_id = "test-user-id"
    team_id = "test-team-id"
    expired_payload = {
        "sub": user_id,
        "team_id": team_id,
        "role": "admin",
        "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=1),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(expired_payload, "test-secret-key", algorithm="HS256")

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] is not None  # expired token error


def test_password_hashing():
    password = "securepassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_team_scoping():
    register_response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "team_name": "Test Team",
        },
    )
    access_token = register_response.json()["access_token"]
    user_data = register_response.json()["user"]

    import jwt as pyjwt

    payload = pyjwt.decode(access_token, "test-secret-key-long-enough-32ch!!", algorithms=["HS256"])
    assert payload["team_id"] == user_data["team_id"]
    assert payload["sub"] == user_data["id"]
    assert payload["role"] == "admin"


def test_token_expiry_values():
    assert ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert REFRESH_TOKEN_EXPIRE_DAYS == 30
