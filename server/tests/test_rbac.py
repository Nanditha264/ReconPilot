import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def get_token_for(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def test_admin_can_access_users_endpoint(client: TestClient):
    """Test that ADMIN role can query /users."""
    token = get_token_for(client, "admin@reconpilot.local", "AdminSecret2026!")
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert "meta" in data["data"]
    assert data["data"]["meta"]["total_items"] >= 3


def test_operator_forbidden_from_admin_users_endpoint(client: TestClient):
    """Test that FINANCE_OPERATOR role cannot access /users which requires ADMIN."""
    token = get_token_for(client, "operator@reconpilot.local", "OperatorSecret2026!")
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "Access denied" in data["error"]["message"]


def test_reviewer_forbidden_from_admin_users_endpoint(client: TestClient):
    """Test that REVIEWER role cannot access /users."""
    token = get_token_for(client, "reviewer@reconpilot.local", "ReviewerSecret2026!")
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False


def test_users_pagination_and_search(client: TestClient):
    """Test pagination parameters and search filtering on /users."""
    token = get_token_for(client, "admin@reconpilot.local", "AdminSecret2026!")

    # Test page_size = 1
    resp = client.get(
        "/api/v1/users?page=1&page_size=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["meta"]["page_size"] == 1
    assert data["data"]["meta"]["has_next"] is True

    # Test search by email
    resp_search = client.get(
        "/api/v1/users?search=operator",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_search.status_code == 200
    search_data = resp_search.json()
    assert len(search_data["data"]["items"]) == 1
    assert search_data["data"]["items"][0]["email"] == "operator@reconpilot.local"
