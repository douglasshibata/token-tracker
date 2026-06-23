from .base import BaseAdapter
from typing import Dict, Any, Tuple
import json

class ClaudeAdapter(BaseAdapter):
    def get_base_url(self) -> str:
        return "https://api.anthropic.com"

    def prepare_request(self, body: Dict[str, Any], api_key: str) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        return f"{self.get_base_url()}/v1/messages", headers, body

    def extract_tokens(self, response_body: Dict[str, Any]) -> Tuple[int, int]:
        usage = response_body.get("usage", {})
        return usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    def detect_tool_use(self, response_body: Dict[str, Any]) -> Tuple[bool, str]:
        content = response_body.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                return True, block.get("name")
        return False, None

    def get_pricing(self, model: str) -> Dict[str, float]:
        # $3 / $15 per MTok for Sonnet 3.5
        return {"input": 3.0, "output": 15.0}
