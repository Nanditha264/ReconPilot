import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def get_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@reconpilot.local", "password": "AdminSecret2026!"},
    )
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def test_reconciliation_run_and_query_results(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trigger reconciliation run
    trigger_resp = client.post(
        "/api/v1/reconciliation/runs",
        headers=headers,
        json={"run_type": "MANUAL_TRIGGER", "tolerance": "1.00"},
    )
    assert trigger_resp.status_code == 200
    run_data = trigger_resp.json()["data"]
    run_id = run_data["id"]
    assert run_data["status"] == "COMPLETED"
    assert run_data["total_records"] > 0
    assert run_data["matched_records"] > 0
    assert run_data["processing_duration_ms"] >= 0

    # 2. List reconciliation runs
    list_resp = client.get("/api/v1/reconciliation/runs", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]["items"]) >= 1

    # 3. Get specific run details
    detail_resp = client.get(f"/api/v1/reconciliation/runs/{run_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["id"] == run_id

    # 4. Get run results
    results_resp = client.get(
        f"/api/v1/reconciliation/runs/{run_id}/results?page=1&page_size=10", headers=headers
    )
    assert results_resp.status_code == 200
    res_items = results_resp.json()["data"]["items"]
    assert len(res_items) <= 10
    assert "expected_amount" in res_items[0]
    assert "actual_amount" in res_items[0]


def test_transactions_endpoints(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/transactions?page=1&page_size=5", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert len(items) > 0
    tx_id = items[0]["id"]

    detail_resp = client.get(f"/api/v1/transactions/{tx_id}", headers=headers)
    assert detail_resp.status_code == 200
    data = detail_resp.json()["data"]
    assert "payment" in data
    assert "fees" in data
    assert "refunds" in data


def test_exceptions_endpoints(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/exceptions?page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert len(items) > 0
    exc_id = items[0]["id"]

    detail_resp = client.get(f"/api/v1/exceptions/{exc_id}", headers=headers)
    assert detail_resp.status_code == 200
    data = detail_resp.json()["data"]
    assert "exception" in data
    assert data["exception"]["id"] == exc_id


def test_idempotent_demo_ingestion_api(client: TestClient):
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/ingestion/demo", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_records_processed"] > 0
    assert data["duration_ms"] >= 0
