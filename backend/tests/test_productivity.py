from app.services.tracking import calculate_productivity_metrics
from decimal import Decimal

def test_productivity_claude_tool_use():
    response = {
        "content": [
            {"type": "text", "text": "I will write the file."},
            {"type": "tool_use", "name": "write_file", "input": {"path": "test.txt", "content": "..."}}
        ]
    }
    metrics = calculate_productivity_metrics("anthropic", response, 100, 200)
    assert metrics["is_tool_call"] is True
    assert metrics["tool_name"] == "write_file"
    assert metrics["generation_ratio"] == 200.0

def test_productivity_gemini_function_call():
    response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"functionCall": {"name": "run_bash", "args": {"command": "ls"}}}
                    ]
                }
            }
        ]
    }
    metrics = calculate_productivity_metrics("gemini", response, 1000, 500)
    assert metrics["is_tool_call"] is True
    assert metrics["tool_name"] == "run_bash"
    assert metrics["generation_ratio"] == 50.0

def test_productivity_chat_only():
    response = {
        "content": [{"type": "text", "text": "Hello!"}]
    }
    metrics = calculate_productivity_metrics("anthropic", response, 100, 10)
    assert metrics["is_tool_call"] is False
    assert metrics["tool_name"] is None
    assert metrics["generation_ratio"] == 10.0
