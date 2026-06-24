from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import time
import os
from datetime import datetime
from uuid import UUID
from .services.database import Database
from .services.pipeline import UnifiedPipeline
from .services.vault import vault
from .services.adapters.claude import ClaudeAdapter
from .services.gatekeeper import estimate_tokens, calculate_estimated_cost, format_error_response
from .routes import projects, logs, export

app = FastAPI(title="Dual-Mode LLM Gateway")
db = Database()
pipeline = UnifiedPipeline(db)
# Shared HTTP client for efficiency
http_client = httpx.AsyncClient()

app.include_router(projects.router, prefix="/v1")
app.include_router(logs.router, prefix="/v1")
app.include_router(export.router, prefix="/v1")

adapters = {
    "claude": ClaudeAdapter(),
}

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    await http_client.aclose()

@app.post("/v1/ingest")
async def ingest_intercepted_request(payload: dict = Body(...)):
    """API for Intercept Mode (MITM/SDK) to report usage"""
    project_id_raw = payload.get("project_id", os.getenv("DEFAULT_PROJECT_ID", "00000000-0000-0000-0000-000000000000"))
    try:
        project_id = UUID(project_id_raw)
    except (ValueError, AttributeError):
        project_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        ts_str = payload.get("timestamp")
        ts = datetime.fromisoformat(ts_str) if ts_str else datetime.utcnow()
    except (ValueError, TypeError):
        ts = datetime.utcnow()

    request_id = await pipeline.ingest_request(
        capture_mode=payload.get("capture_mode", "intercept"),
        method=payload.get("method", "unknown"),
        provider_name=payload.get("provider_name"),
        model=payload.get("model", "unknown"),
        user_id=None, # Will be resolved via IP
        request_body=payload.get("request_body", {}),
        input_tokens=payload.get("input_tokens", 0),
        output_tokens=payload.get("output_tokens", 0),
        latency_ms=payload.get("latency_ms", 0),
        timestamp=ts,
        source_ip=payload.get("source_ip"),
        status=payload.get("status", "success"),
        project_id=project_id,
        is_tool_call=payload.get("is_tool_call", False),
        tool_name=payload.get("tool_name")
    )
    return {"request_id": str(request_id)}

@app.api_route("/v1/chat/completions", methods=["POST"])
async def gateway_proxy(request: Request):
    """Active Gateway Mode: OpenAI-compatible endpoint with HARD BLOCKING"""
    source_ip = request.client.host if request.client else "127.0.0.1"
    user_id = UUID(os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000000"))

    body = await request.json()
    model = body.get("model", "claude-3-5-sonnet-20241022")

    # 1. PRE-REQUEST BLOCKING LOGIC
    # Estimate tokens and cost before calling the real API
    est_tokens = estimate_tokens(body)
    # Simplified provider determination
    provider_name = "claude" if "claude" in model else "google"
    est_cost = calculate_estimated_cost(provider_name, model, est_tokens)

    # Project ID from header or default
    project_id_raw = request.headers.get("X-Project-ID", os.getenv("DEFAULT_PROJECT_ID", "00000000-0000-0000-0000-000000000000"))
    try:
        project_id = UUID(project_id_raw)
    except (ValueError, AttributeError):
        project_id = UUID("00000000-0000-0000-0000-000000000000")

    # Check budget for the user/project
    budget_status = await db.check_budget(user_id, est_cost)
    if not budget_status["allowed"]:
        reason = budget_status["reason"]
        # Log the blocked attempt
        await pipeline.ingest_request(
            capture_mode="gateway", method="proxy", provider_name=provider_name,
            model=model, user_id=user_id, request_body=body,
            input_tokens=est_tokens, output_tokens=0, latency_ms=0,
            timestamp=datetime.utcnow(), source_ip=source_ip, status="blocked",
            project_id=project_id
        )
        return JSONResponse(status_code=429, content=format_error_response(provider_name, reason))

    # 2. FORWARD TO PROVIDER
    adapter = adapters.get(provider_name)
    if not adapter:
        return JSONResponse(status_code=400, content={"error": f"No adapter for provider: {provider_name}"})

    api_key = os.getenv("ANTHROPIC_API_KEY", "mock-key")
    url, headers, provider_body = adapter.prepare_request(body, api_key)

    start_time = time.time()
    timestamp = datetime.utcnow()

    if body.get("stream"):
        async def stream_gen():
            async with http_client.stream("POST", url, headers=headers, json=provider_body) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk
        return StreamingResponse(stream_gen(), media_type="text/event-stream")

    try:
        resp = await http_client.post(url, headers=headers, json=provider_body, timeout=60.0)
        latency_ms = int((time.time() - start_time) * 1000)

        if resp.status_code == 200:
            resp_data = resp.json()
            in_tok, out_tok = adapter.extract_tokens(resp_data)
            is_tool, tool_name = adapter.detect_tool_use(resp_data)

            await pipeline.ingest_request(
                capture_mode="gateway",
                method="proxy",
                provider_name=provider_name,
                model=model,
                user_id=user_id,
                request_body=body,
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_ms=latency_ms,
                timestamp=timestamp,
                source_ip=source_ip,
                project_id=project_id,
                is_tool_call=is_tool,
                tool_name=tool_name
            )
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": f"Gateway Error: {str(e)}"})
