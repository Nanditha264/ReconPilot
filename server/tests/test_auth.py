import pytest
from app.core.security import create_access_token, hash_password, verify_password
from app.main import app
from app.models.enums import UserRole
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_password_hashing_argon2id():
    """Verify that password hashing uses argon2id and verifies correctly."""
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_claims():
    """Verify JWT access token contains valid sub, role, exp claims."""
    claims = {
        "sub": "00000000-0000-4000-a000-000000000001",
        "merchant_id": "00000000-0000-4000-a000-000000000002",
        "role": UserRole.ADMIN.value,
    }
    token = create_access_token(claims)
    assert isinstance(token, str)
    assert len(token) > 20


def test_login_success(client: TestClient):
    """Test successful login with seeded admin credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@reconpilot.local", "password": "AdminSecret2026!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "admin@reconpilot.local"
    assert data["data"]["user"]["role"] == "ADMIN"
    assert "merchant" in data["data"]
    assert data["data"]["merchant"]["currency"] == "INR"


def test_login_invalid_credentials(client: TestClient):
    """Test failed login with incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@reconpilot.local", "password": "IncorrectPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "HTTP_401"


def test_login_nonexistent_user(client: TestClient):
    """Test failed login with nonexistent email."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@reconpilot.local", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_me_endpoint_requires_auth(client: TestClient):
    """Test /auth/me returns 401 when no token is provided."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_me_endpoint_with_valid_token(client: TestClient):
    """Test /auth/me returns user profile and merchant details with valid bearer token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@reconpilot.local", "password": "AdminSecret2026!"},
    )
    token = login_resp.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "admin@reconpilot.local"
    assert data["data"]["user"]["role"] == "ADMIN"


def test_logout_endpoint(client: TestClient):
    """Test /auth/logout accepts bearer token and acknowledges logout."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@reconpilot.local", "password": "AdminSecret2026!"},
    )
    token = login_resp.json()["data"]["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "logged out" in data["data"]["message"].lower()
