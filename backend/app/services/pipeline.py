import hashlib
import json
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class UnifiedPipeline:
    def __init__(self, db):
        self.db = db

    def generate_fingerprint(self, source_ip: str, model: str, input_tokens: int, timestamp: str) -> str:
        # Generate SHA256 of identifying traits to detect same request seen via different modes
        # Timestamp truncated to 5s window to handle slight delays between proxy and sniffer
        # In a real app, use request body hash if available
        payload = f"{source_ip}:{model}:{input_tokens}:{timestamp[:18]}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def get_user_for_ip(self, ip_address: str) -> Optional[UUID]:
        if not self.db.pool: await self.db.connect()
        async with self.db.pool.acquire() as conn:
            return await conn.fetchval("SELECT user_id FROM ip_user_mapping WHERE ip_address = $1 AND is_active = TRUE", ip_address)

    async def ingest_request(
        self,
        capture_mode: str, # 'gateway', 'intercept-mitm', 'intercept-sdk'
        method: str,       # 'proxy', 'mitm'
        provider_name: str,
        model: str,
        user_id: Optional[UUID],
        request_body: Dict[str, Any],
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        timestamp: datetime,
        source_ip: str,
        status: str = "success"
    ):
        if not self.db.pool: await self.db.connect()

        # 1. Deduplication
        fingerprint = self.generate_fingerprint(source_ip, model, input_tokens, str(timestamp))

        async with self.db.pool.acquire() as conn:
            # Check if this request was already logged (e.g. by Gateway, and now by MITM)
            existing_request = await conn.fetchrow("SELECT request_id, capture_mode FROM request_fingerprints WHERE fingerprint = $1", fingerprint)

            if existing_request:
                # If Gateway already logged it, ignore the Intercept record (Gateway has more metadata)
                if existing_request['capture_mode'] == 'gateway' and capture_mode != 'gateway':
                    return existing_request['request_id']
                # If Intercept logged it first, and now Gateway sees it, maybe update?
                # For simplicity, we just skip duplicates.
                return existing_request['request_id']

            # 2. User Resolution for Intercept mode
            if not user_id and source_ip:
                user_id = await conn.fetchval("SELECT user_id FROM ip_user_mapping WHERE ip_address = $1 AND is_active = TRUE", source_ip)
                # If still no user, use default or leave as NULL for Discovery
                if not user_id:
                    user_id = UUID('00000000-0000-0000-0000-000000000000')

            # 3. Calculate Cost
            total_cost = (Decimal(input_tokens + output_tokens) / Decimal(1_000_000)) * Decimal(5.0)

            # 4. Write Unified Log
            request_id = await conn.fetchval("""
                INSERT INTO requests
                (capture_mode, method, user_id, provider_id, model,
                 request_messages, status, input_tokens, output_tokens,
                 total_cost, latency_ms, source_ip, created_at)
                VALUES ($1, $2, $3, (SELECT id FROM providers WHERE name = $4), $5,
                        $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
            """, capture_mode, method, user_id, provider_name, model,
            json.dumps(request_body.get("messages", [])), status, input_tokens, output_tokens,
            total_cost, latency_ms, source_ip, timestamp)

            # 5. Store Fingerprint
            await conn.execute("""
                INSERT INTO request_fingerprints (fingerprint, request_id, capture_mode)
                VALUES ($1, $2, $3)
            """, fingerprint, request_id, capture_mode)

            # 6. Budget Enforcement (Gateway Mode Only)
            if capture_mode == "gateway":
                await conn.execute("""
                    UPDATE budgets
                    SET cost_used = cost_used + $1
                    WHERE entity_id = $2 OR entity_type = 'company'
                """, total_cost, str(user_id))

            return request_id
