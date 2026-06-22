from app.services.gatekeeper import estimate_tokens, calculate_estimated_cost
from app.services.tracking import calculate_cost
from decimal import Decimal

def test_token_estimation():
    body = {
        "messages": [
            {"role": "user", "content": "Hello, world!"} # 13 chars
        ]
    }
    # 13 // 4 = 3 tokens
    assert estimate_tokens(body) == 3

def test_cost_calculation():
    # claude-3-5-sonnet: 3.0 input, 15.0 output per MTok
    # 1M input tokens = $3.0
    input_tokens = 1_000_000
    output_tokens = 1_000_000

    in_cost, out_cost = calculate_cost("claude", "claude-3-5-sonnet-20241022", input_tokens, output_tokens)

    assert in_cost == Decimal("3.0")
    assert out_cost == Decimal("15.0")

def test_estimated_cost():
    # 1M input tokens. Estimated cost assumes 2M output tokens.
    # 1M * 3.0 + 2M * 15.0 = 3.0 + 30.0 = 33.0
    cost = calculate_estimated_cost("claude", "claude-3-5-sonnet-20241022", 1_000_000)
    assert cost == 33.0
