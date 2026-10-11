import pytest
from app.core.config import get_settings
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_liveness(client: TestClient):
    """Test that /api/v1/health returns HTTP 200, status healthy, and configuration details."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "reconpilot-backend"
    assert data["data"]["version"] == "0.1.0"
    assert "integrations" in data["data"]
    assert data["data"]["integrations"]["ai_provider"] == "mock"


def test_health_readiness_reports_truthful_state(client: TestClient):
    """
    Test that /api/v1/health/ready accurately reports database state without faking.
    If PostgreSQL is unreachable, it must return 503 and success: false.
    If PostgreSQL is running, it returns 200 and success: true.
    """
    response = client.get("/api/v1/health/ready")
    data = response.json()
    if response.status_code == 200:
        assert data["success"] is True
        assert data["data"]["status"] == "ready"
        assert data["data"]["database"]["connected"] is True
    else:
        assert response.status_code == 503
        assert data["success"] is False
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert data["error"]["details"]["database"]["type"] == "PostgreSQL"
        assert data["error"]["details"]["database"]["connected"] is False


def test_settings_defaults():
    """Verify default development configuration settings."""
    settings = get_settings()
    assert settings.APP_ENV == "development"
    assert "postgresql" in settings.DATABASE_URL
    assert settings.AMOUNT_TOLERANCE == 1.00
    assert settings.AI_AUTO_CLASSIFY_THRESHOLD == 0.90
    assert settings.AI_REVIEW_THRESHOLD == 0.75
    # Dev settings without configured secrets
    assert settings.has_razorpay_credentials is False
    assert settings.has_llm_credentials is False
