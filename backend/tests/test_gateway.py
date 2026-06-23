import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import AsyncMock, patch
from uuid import UUID
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def mock_pipeline():
    with patch("app.main.pipeline.ingest_request") as mock:
        mock.return_value = AsyncMock(return_value=UUID("00000000-0000-0000-0000-00000000000A"))
        yield mock

def test_gateway_proxy_claude(mock_pipeline):
    with patch("app.main.http_client.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"usage": {"input_tokens": 10, "output_tokens": 20}, "content": []},
            content=b'{"usage": {"input_tokens": 10, "output_tokens": 20}}',
            headers={}
        )

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "hello"}]
        }
        response = client.post("/v1/chat/completions", json=payload)

        assert response.status_code == 200
        mock_pipeline.assert_called_once()
        # Verify it was logged as gateway source
        args, kwargs = mock_pipeline.call_args
        assert kwargs['capture_mode'] == "gateway"

def test_ingest_intercept_mitm(mock_pipeline):
    payload = {
        "capture_mode": "intercept-mitm",
        "method": "mitm",
        "provider_name": "anthropic",
        "model": "claude-3",
        "source_ip": "10.0.0.1",
        "input_tokens": 100,
        "output_tokens": 50,
        "latency_ms": 500,
        "request_body": {"messages": []},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = client.post("/v1/ingest", json=payload)
    assert response.status_code == 200
    mock_pipeline.assert_called_once()
    args, kwargs = mock_pipeline.call_args
    assert kwargs['capture_mode'] == "intercept-mitm"
