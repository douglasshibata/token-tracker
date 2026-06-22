import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.database import Database
from unittest.mock import AsyncMock, MagicMock, patch
import json
from uuid import UUID

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("app.main.db") as mock:
        mock.check_budget = AsyncMock(return_value={"allowed": True})
        mock.get_or_create_session = AsyncMock(return_value=UUID("00000000-0000-0000-0000-000000000001"))
        mock.log_request = AsyncMock()
        yield mock

@pytest.fixture
def mock_httpx():
    with patch("app.main.http_client.request") as mock:
        mock.return_value = MagicMock(
            status_code=200,
            json=lambda: {"usage": {"input_tokens": 10, "output_tokens": 20}, "content": []},
            content=b'{"usage": {"input_tokens": 10, "output_tokens": 20}}',
            headers={}
        )
        yield mock

def test_proxy_interception_success(mock_db, mock_httpx):
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "test"}]
    }
    response = client.post("/v1/messages", json=payload, headers={"X-Project-Id": "00000000-0000-0000-0000-000000000000"})

    assert response.status_code == 200
    mock_db.check_budget.assert_called_once()
    mock_db.log_request.assert_called_once()

def test_proxy_blocking(mock_db):
    mock_db.check_budget = AsyncMock(return_value={"allowed": False, "reason": "Budget Exceeded"})

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "test"}]
    }
    response = client.post("/v1/messages", json=payload, headers={"X-Project-Id": "00000000-0000-0000-0000-000000000000"})

    assert response.status_code == 429
    assert "Budget Exceeded" in response.json()["error"]["message"]

def test_create_project(mock_db):
    mock_db.pool = MagicMock()
    mock_db.pool.acquire = MagicMock()

    # Mocking async context manager
    mock_conn = AsyncMock()
    mock_db.pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Test Project",
        "description": "Test Desc",
        "daily_limit": 10.0,
        "monthly_limit": 100.0,
        "total_limit": 500.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }

    payload = {
        "name": "Test Project",
        "description": "Test Desc",
        "daily_limit": 10.0,
        "monthly_limit": 100.0,
        "total_limit": 500.0
    }

    with patch("app.routes.projects.db", mock_db):
        response = client.post("/v1/projects/", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"
