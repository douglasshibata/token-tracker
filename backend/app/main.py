from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx
import json
import time
from .services.database import Database
from .services.gatekeeper import estimate_tokens, calculate_estimated_cost, format_error_response
from .services.tracking import extract_token_usage, calculate_cost, calculate_productivity_metrics
from .api.routes import projects, logs
import os

app = FastAPI(title="Token Tracker Gatekeeper Proxy")
db = Database()

# Use a persistent client pool for efficiency
http_client = httpx.AsyncClient()

app.include_router(projects.router, prefix="/v1")
app.include_router(logs.router, prefix="/v1")

PROVIDERS_URLS = {
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
    "kiro": "https://generativelanguage.googleapis.com", # Kiro routes to Gemini/AWS
    "antigravity": "https://api.antigravity.ai"
}

def get_target_provider(path: str) -> str:
    if "anthropic" in path or "claude" in path: return "anthropic"
    if "gemini" in path or "google" in path: return "gemini"
    if "kiro" in path: return "kiro"
    return "antigravity"

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    await http_client.aclose()

@app.api_route("/{path:path}", methods=["POST", "GET", "PUT", "DELETE"])
async def proxy_interceptor(request: Request, path: str):
    provider = get_target_provider(path)
    project_id = request.headers.get("X-Project-Id", "00000000-0000-0000-0000-000000000000")
    source = request.headers.get("X-Source", "unknown")
    session_id_header = request.headers.get("X-Session-Id")

    if request.method == "POST":
        try:
            body = await request.json()
        except:
            body = {}

        model = body.get("model", "unknown")
        estimated_input_tokens = estimate_tokens(body)
        estimated_max_cost = calculate_estimated_cost(provider, model, estimated_input_tokens)

        budget_status = await db.check_budget(project_id, estimated_max_cost)

        if not budget_status["allowed"]:
            reason = budget_status["reason"]
            await db.log_request(
                project_id=project_id, provider=provider, model=model,
                was_blocked=True, block_reason=reason, metadata=body
            )
            return JSONResponse(
                status_code=429,
                content=format_error_response(provider, reason)
            )

    # Get or create session
    session_uuid = await db.get_or_create_session(project_id, source, session_id_header)

    headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}
    base_url = PROVIDERS_URLS.get(provider, PROVIDERS_URLS["antigravity"])
    target_url = f"{base_url}/{path}"

    start_time = time.time()

    content = await request.body()
    try:
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=content,
            params=request.query_params,
            timeout=60.0
        )
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": f"Gateway Error: {str(e)}"})

    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200 and request.method == "POST":
        try:
            resp_data = response.json()
            input_tokens, output_tokens = extract_token_usage(provider, resp_data)
            actual_input_cost, actual_output_cost = calculate_cost(provider, model, input_tokens, output_tokens)
            total_cost = float(actual_input_cost + actual_output_cost)

            # Productivity Metrics
            prod_metrics = calculate_productivity_metrics(provider, resp_data, input_tokens, output_tokens)

            await db.log_request(
                project_id=project_id, session_id=session_uuid, provider=provider, model=model,
                input_tokens=input_tokens, output_tokens=output_tokens,
                cost=total_cost, latency_ms=latency_ms,
                is_tool_call=prod_metrics["is_tool_call"],
                tool_name=prod_metrics["tool_name"],
                generation_ratio=prod_metrics["generation_ratio"],
                metadata={"request": body, "response": resp_data}
            )
        except Exception as e:
            print(f"Error logging successful request: {e}")

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
