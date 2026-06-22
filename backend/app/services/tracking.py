from typing import Tuple, Dict, Any
from decimal import Decimal

def extract_token_usage(provider: str, response: dict) -> Tuple[int, int]:
    """Extract token counts from different provider response formats"""
    if provider == "anthropic":
        usage = response.get("usage", {})
        return (
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0)
        )
    elif provider == "gemini" or provider == "kiro":
        usage_metadata = response.get("usageMetadata", {})
        return (
            usage_metadata.get("promptTokenCount", 0),
            usage_metadata.get("candidatesTokenCount", 0)
        )
    elif provider == "antigravity":
        usage = response.get("usage", {})
        return (
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0)
        )
    return (0, 0)

PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}

DEFAULT_RATES = {"input": 5.0, "output": 15.0}

def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> Tuple[Decimal, Decimal]:
    """Calculate input and output costs based on provider and model"""
    pricing = PRICING.get(model, DEFAULT_RATES)

    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * Decimal(pricing["input"])
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * Decimal(pricing["output"])

    return input_cost, output_cost

def calculate_productivity_metrics(provider: str, response_body: Dict[str, Any], input_tokens: int, output_tokens: int) -> Dict[str, Any]:
    """Calculate productivity metrics like tool use detection and generation ratio"""
    is_tool_call = False
    tool_name = None

    if provider == "anthropic":
        content_blocks = response_body.get("content", [])
        if isinstance(content_blocks, list):
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    is_tool_call = True
                    tool_name = block.get("name")
                    break

    elif provider == "gemini" or provider == "kiro":
        candidates = response_body.get("candidates", [])
        if isinstance(candidates, list):
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and "functionCall" in part:
                        is_tool_call = True
                        tool_name = part["functionCall"].get("name")
                        break

    generation_ratio = (output_tokens / input_tokens * 100) if input_tokens > 0 else 0

    return {
        "is_tool_call": is_tool_call,
        "tool_name": tool_name,
        "generation_ratio": round(generation_ratio, 2)
    }
