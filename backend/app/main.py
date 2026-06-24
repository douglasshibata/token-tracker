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


def detect_source_tool(request: Request) -> str:
    """Detect which AI tool/IDE is making the request based on headers and user-agent."""
    user_agent = (request.headers.get("user-agent") or "").lower()
    x_source = request.headers.get("x-source", "").lower()

    # Explicit header (set by user in env vars)
    if x_source:
        return x_source

    # Claude CLI detection
    if "claude" in user_agent or "anthropic-cli" in user_agent:
        return "claude-cli"

    # Kiro / AWS Q detection
    if "kiro" in user_agent or "aws-q" in user_agent or "amazon" in user_agent:
        return "kiro"

    # Antigravity detection
    if "antigravity" in user_agent:
        return "antigravity"

    # Cursor detection
    if "cursor" in user_agent:
        return "cursor"

    # VS Code / Generic IDE
    if "vscode" in user_agent or "visual-studio" in user_agent:
        return "vscode"

    # Node.js based clients (likely an IDE extension)
    if "node" in user_agent:
        return "ide-extension"

    # Python SDK (could be scripts or automation)
    if "python" in user_agent:
        return "python-sdk"

    return "unknown"

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

    # Source type: which AI IDE sent this request
    source_type = payload.get("source_type", payload.get("method", "api"))

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
        tool_name=payload.get("tool_name"),
        source_type=source_type
    )
    return {"request_id": str(request_id)}

@app.api_route("/v1/messages", methods=["POST"])
async def anthropic_gateway_proxy(request: Request):
    """Active Gateway Mode: Anthropic /v1/messages endpoint (used by Claude CLI, Kiro)"""
    source_ip = request.client.host if request.client else "127.0.0.1"
    user_id = UUID(os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000000"))

    body = await request.json()
    model = body.get("model", "claude-sonnet-4-20250514")

    # Detect source type from headers
    source_type = detect_source_tool(request)

    # Estimate tokens from messages
    est_tokens = estimate_tokens(body)
    est_cost = calculate_estimated_cost("claude", model, est_tokens)

    # Project ID from header or default
    project_id_raw = request.headers.get("X-Project-ID", os.getenv("DEFAULT_PROJECT_ID", "00000000-0000-0000-0000-000000000000"))
    try:
        project_id = UUID(project_id_raw)
    except (ValueError, AttributeError):
        project_id = UUID("00000000-0000-0000-0000-000000000000")

    # Check budget
    budget_status = await db.check_budget(user_id, est_cost)
    if not budget_status["allowed"]:
        reason = budget_status["reason"]
        await pipeline.ingest_request(
            capture_mode="gateway", method="proxy", provider_name="claude",
            model=model, user_id=user_id, request_body=body,
            input_tokens=est_tokens, output_tokens=0, latency_ms=0,
            timestamp=datetime.utcnow(), source_ip=source_ip, status="blocked",
            project_id=project_id, source_type=source_type
        )
        return JSONResponse(status_code=429, content={"type": "error", "error": {"type": "rate_limit_error", "message": reason}})

    # Forward to real Anthropic API
    adapter = adapters["claude"]
    api_key = request.headers.get("x-api-key") or os.getenv("ANTHROPIC_API_KEY", "")
    url, headers, provider_body = adapter.prepare_request(body, api_key)

    # Preserve anthropic-version and other headers from original request
    if request.headers.get("anthropic-version"):
        headers["anthropic-version"] = request.headers["anthropic-version"]
    if request.headers.get("anthropic-beta"):
        headers["anthropic-beta"] = request.headers["anthropic-beta"]

    start_time = time.time()
    timestamp = datetime.utcnow()

    # Handle streaming
    if body.get("stream"):
        collected_input_tokens = 0
        collected_output_tokens = 0
        is_tool = False
        tool_name_found = None

        async def stream_and_track():
            nonlocal collected_input_tokens, collected_output_tokens, is_tool, tool_name_found
            try:
                async with http_client.stream("POST", url, headers=headers, json=provider_body, timeout=120.0) as resp:
                    async for chunk in resp.aiter_bytes():
                        # Try to extract usage from SSE events
                        chunk_str = chunk.decode("utf-8", errors="ignore")
                        if "message_delta" in chunk_str and '"usage"' in chunk_str:
                            try:
                                import re
                                usage_match = re.search(r'"output_tokens"\s*:\s*(\d+)', chunk_str)
                                if usage_match:
                                    collected_output_tokens = int(usage_match.group(1))
                            except Exception:
                                pass
                        if "message_start" in chunk_str and '"usage"' in chunk_str:
                            try:
                                import re
                                input_match = re.search(r'"input_tokens"\s*:\s*(\d+)', chunk_str)
                                if input_match:
                                    collected_input_tokens = int(input_match.group(1))
                            except Exception:
                                pass
                        if '"type":"tool_use"' in chunk_str or '"type": "tool_use"' in chunk_str:
                            is_tool = True
                            try:
                                import re
                                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', chunk_str)
                                if name_match:
                                    tool_name_found = name_match.group(1)
                            except Exception:
                                pass
                        yield chunk
            finally:
                # Log after stream completes
                latency_ms = int((time.time() - start_time) * 1000)
                final_input = collected_input_tokens if collected_input_tokens > 0 else est_tokens
                await pipeline.ingest_request(
                    capture_mode="gateway", method="proxy", provider_name="claude",
                    model=model, user_id=user_id, request_body=body,
                    input_tokens=final_input, output_tokens=collected_output_tokens,
                    latency_ms=latency_ms, timestamp=timestamp, source_ip=source_ip,
                    project_id=project_id, is_tool_call=is_tool, tool_name=tool_name_found,
                    source_type=source_type
                )

        return StreamingResponse(stream_and_track(), media_type="text/event-stream")

    # Non-streaming
    try:
        resp = await http_client.post(url, headers=headers, json=provider_body, timeout=120.0)
        latency_ms = int((time.time() - start_time) * 1000)

        if resp.status_code == 200:
            resp_data = resp.json()
            in_tok, out_tok = adapter.extract_tokens(resp_data)
            is_tool, tool_name_val = adapter.detect_tool_use(resp_data)

            await pipeline.ingest_request(
                capture_mode="gateway", method="proxy", provider_name="claude",
                model=model, user_id=user_id, request_body=body,
                input_tokens=in_tok, output_tokens=out_tok,
                latency_ms=latency_ms, timestamp=timestamp, source_ip=source_ip,
                project_id=project_id, is_tool_call=is_tool, tool_name=tool_name_val,
                source_type=source_type
            )

        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"type": "error", "error": {"type": "api_error", "message": f"Gateway Error: {str(e)}"}})


@app.api_route("/v1/chat/completions", methods=["POST"])
async def gateway_proxy(request: Request):
    """Active Gateway Mode: OpenAI-compatible endpoint with HARD BLOCKING"""
    source_ip = request.client.host if request.client else "127.0.0.1"
    user_id = UUID(os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000000"))

    body = await request.json()
    model = body.get("model", "claude-3-5-sonnet-20241022")

    # Detect source type from headers/user-agent
    source_type = detect_source_tool(request)

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
            project_id=project_id, source_type=source_type
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
                tool_name=tool_name,
                source_type=source_type
            )
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": f"Gateway Error: {str(e)}"})
