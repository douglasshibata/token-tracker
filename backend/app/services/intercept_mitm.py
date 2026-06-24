import json
import requests
from mitmproxy import http, ctx
from datetime import datetime

# Domain mapping for interception
INTERCEPT_DOMAINS = [
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "bedrock-runtime",       # AWS Bedrock (Kiro)
    "invoke-model",          # AWS Bedrock invoke
    "q.us-east-1.amazonaws", # AWS Q / Kiro
]

INGEST_URL = "http://localhost:8000/v1/ingest"


class LLMInterceptAddon:
    def __init__(self):
        self.ingest_url = INGEST_URL

    def request(self, flow: http.HTTPFlow):
        host = flow.request.pretty_host
        if not any(d in host for d in INTERCEPT_DOMAINS):
            return

        # Extract Request Info
        try:
            body = json.loads(flow.request.get_text())
        except Exception:
            body = {}

        # Determine provider
        if "anthropic" in host:
            provider = "anthropic"
        elif "bedrock" in host or "amazonaws" in host:
            provider = "anthropic"  # Kiro uses Claude via Bedrock
        elif "google" in host:
            provider = "google"
        else:
            provider = "unknown"

        # Detect source IDE from user-agent
        user_agent = flow.request.headers.get("user-agent", "").lower()
        source_type = flow.request.headers.get("x-source", "")
        if not source_type:
            if "kiro" in user_agent:
                source_type = "kiro"
            elif "antigravity" in user_agent:
                source_type = "antigravity"
            elif "cursor" in user_agent:
                source_type = "cursor"
            elif "claude" in user_agent:
                source_type = "claude-cli"
            elif "vscode" in user_agent:
                source_type = "vscode"
            else:
                source_type = "unknown"

        flow.metadata["llm_intercept"] = {
            "source_ip": flow.client_conn.peername[0] if flow.client_conn.peername else "127.0.0.1",
            "provider": provider,
            "model": body.get("model", body.get("modelId", "unknown")),
            "request_body": body,
            "start_time": flow.timestamp_start,
            "is_tool_call": False,
            "tool_name": None,
            "source_type": source_type,
        }

    def response(self, flow: http.HTTPFlow):
        if "llm_intercept" not in flow.metadata:
            return

        capture = flow.metadata["llm_intercept"]
        latency_ms = int((flow.timestamp_end - capture["start_time"]) * 1000)

        try:
            resp_body = json.loads(flow.response.get_text())
        except Exception:
            resp_body = {}

        # Token extraction
        in_tok, out_tok = 0, 0
        is_tool = False
        tool_name = None

        if capture["provider"] == "anthropic":
            usage = resp_body.get("usage", {})
            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
            # Detect tool use
            for block in resp_body.get("content", []):
                if block.get("type") == "tool_use":
                    is_tool = True
                    tool_name = block.get("name")
                    break
        elif capture["provider"] == "google":
            usage = resp_body.get("usageMetadata", {})
            in_tok = usage.get("promptTokenCount", 0)
            out_tok = usage.get("candidatesTokenCount", 0)

        # Report to backend
        payload = {
            "capture_mode": "intercept-mitm",
            "method": "mitm",
            "provider_name": capture["provider"],
            "model": capture["model"],
            "source_ip": capture["source_ip"],
            "source_type": capture["source_type"],
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "latency_ms": latency_ms,
            "request_body": {"messages": capture["request_body"].get("messages", [])[:1]},  # Only first msg to save space
            "timestamp": datetime.fromtimestamp(capture["start_time"]).isoformat(),
            "is_tool_call": is_tool,
            "tool_name": tool_name,
            "status": "success" if flow.response.status_code == 200 else "error",
        }

        try:
            requests.post(self.ingest_url, json=payload, timeout=5)
            ctx.log.info(f"[TRACKED] {capture['provider']} | {capture['model']} | {in_tok}+{out_tok} tokens | ${(in_tok+out_tok)*5/1_000_000:.4f}")
        except Exception as e:
            ctx.log.warn(f"[TRACK FAILED] {e}")


addons = [LLMInterceptAddon()]
