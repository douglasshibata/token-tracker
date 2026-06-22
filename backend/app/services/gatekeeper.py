from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}

DEFAULT_RATES = {"input": 5.0, "output": 15.0}

def estimate_tokens(request_body: Dict[str, Any]) -> int:
    """Rough estimation: 1 token ~ 4 characters"""
    chars = 0
    # Anthropic/Gemini standard messages format
    messages = request_body.get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    chars += len(part.get("text", ""))

    # Also count system prompt if present
    system = request_body.get("system", "")
    if isinstance(system, str):
        chars += len(system)

    return chars // 4

def calculate_estimated_cost(provider: str, model: str, input_tokens: int) -> float:
    """Estimate cost assuming output is roughly 2x input for safety margin"""
    rates = PRICING.get(model, DEFAULT_RATES)
    output_tokens = input_tokens * 2

    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]

    return input_cost + output_cost

async def check_budget_status(db, project_id: str, estimated_max_cost: float) -> Dict[str, Any]:
    """Check if the project has enough budget for the estimated cost"""
    # This will call the database service
    return await db.check_budget(project_id, estimated_max_cost)

def format_error_response(provider: str, reason: str) -> Dict[str, Any]:
    """Format a 429 error response mimicking the target provider's style"""
    message = f"Token Tracker Budget Limit Exceeded: {reason}"

    if provider == "anthropic":
        return {
            "type": "error",
            "error": {
                "type": "rate_limit_error",
                "message": message
            }
        }
    elif provider == "gemini":
        return {
            "error": {
                "code": 429,
                "message": message,
                "status": "RESOURCE_EXHAUSTED"
            }
        }
    else: # Default/Antigravity style
        return {
            "error": {
                "message": message,
                "code": "budget_exceeded"
            }
        }
