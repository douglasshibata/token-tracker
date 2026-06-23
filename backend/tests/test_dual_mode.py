import pytest
from app.services.pipeline import UnifiedPipeline
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from datetime import datetime

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.pool = MagicMock()
    # Mock pool.acquire() as an async context manager
    mock_conn = AsyncMock()
    db.pool.acquire.return_value.__aenter__.return_value = mock_conn
    return db, mock_conn

@pytest.mark.asyncio
async def test_deduplication_logic(mock_db):
    db, conn = mock_db
    pipeline = UnifiedPipeline(db)

    user_id = UUID("00000000-0000-0000-0000-000000000001")
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    source_ip = "10.0.0.1"

    # 1. Mock first call (Gateway)
    # Fingerprint check returns None
    conn.fetchrow.return_value = None
    # Ingest returns a new ID
    conn.fetchval.return_value = UUID("00000000-0000-0000-0000-00000000000A")

    req_id_1 = await pipeline.ingest_request(
        capture_mode="gateway", method="proxy", provider_name="anthropic",
        model="claude-3", user_id=user_id, request_body={"messages": []},
        input_tokens=100, output_tokens=50, latency_ms=500,
        timestamp=timestamp, source_ip=source_ip
    )

    # 2. Mock second call (Intercept) - same fingerprint
    # Fingerprint check returns the existing record
    conn.fetchrow.return_value = {"request_id": req_id_1, "capture_mode": "gateway"}

    req_id_2 = await pipeline.ingest_request(
        capture_mode="intercept-mitm", method="mitm", provider_name="anthropic",
        model="claude-3", user_id=None, request_body={"messages": []},
        input_tokens=100, output_tokens=50, latency_ms=510,
        timestamp=timestamp, source_ip=source_ip
    )

    assert req_id_1 == req_id_2
    # Verify insert (fetchval) only called once
    assert conn.fetchval.call_count == 1
