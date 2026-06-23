import json
import requests
from mitmproxy import http, ctx
from datetime import datetime

# Domain mapping for interception
INTERCEPT_DOMAINS = [
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
]

class LLMInterceptAddon:
    def __init__(self, backend_url):
        self.backend_url = backend_url

    def request(self, flow: http.HTTPFlow):
        host = flow.request.pretty_host
        if not any(d in host for d in INTERCEPT_DOMAINS):
            return

        # 1. Redact Client API Key
        for h in ["x-api-key", "authorization"]:
            if h in flow.request.headers:
                flow.request.headers[h] = "[REDACTED]"

        # 2. Extract Request Info
        try:
            body = json.loads(flow.request.get_text())
        except:
            body = {}

        flow.metadata["llm_intercept"] = {
            "source_ip": flow.client_conn.peername[0],
            "provider": "anthropic" if "anthropic" in host else "google",
            "model": body.get("model", "unknown"),
            "request_body": body,
            "start_time": flow.timestamp_start,
        }

    def response(self, flow: http.HTTPFlow):
        if "llm_intercept" not in flow.metadata:
            return

        capture = flow.metadata["llm_intercept"]
        latency_ms = int((flow.timestamp_end - capture["start_time"]) * 1000)

        try:
            resp_body = json.loads(flow.response.get_text())
        except:
            resp_body = {}

        # 3. Simple token extraction
        in_tok, out_tok = 0, 0
        if capture["provider"] == "anthropic":
            usage = resp_body.get("usage", {})
            in_tok, out_tok = usage.get("input_tokens", 0), usage.get("output_tokens", 0)

        # 4. Report to Unified Backend (Simulated async call)
        payload = {
            "capture_mode": "intercept-mitm",
            "method": "mitm",
            "provider_name": capture["provider"],
            "model": capture["model"],
            "source_ip": capture["source_ip"],
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "latency_ms": latency_ms,
            "request_body": capture["request_body"],
            "timestamp": datetime.fromtimestamp(capture["start_time"]).isoformat()
        }

        # In real app: requests.post(f"{self.backend_url}/v1/ingest", json=payload)
        ctx.log.info(f"[INTERCEPT] {capture['provider']} | {capture['model']} | {in_tok}+{out_tok} tokens")

addons = [LLMInterceptAddon("http://backend:8000")]
