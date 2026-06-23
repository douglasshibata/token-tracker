import functools
import time
import requests
from datetime import datetime

# Conceptual Python SDK Wrapper
# Demonstrates how to intercept at code-level using monkeypatching

def wrap_anthropic_create(original_create_func):
    @functools.wraps(original_create_func)
    def wrapped(*args, **kwargs):
        start_time = time.time()
        model = kwargs.get("model", "unknown")

        # 1. Call Real SDK
        response = original_create_func(*args, **kwargs)

        # 2. Extract Data
        latency_ms = int((time.time() - start_time) * 1000)
        usage = getattr(response, 'usage', {})
        in_tok = getattr(usage, 'input_tokens', 0)
        out_tok = getattr(usage, 'output_tokens', 0)

        # 3. Report to Backend (Passive)
        payload = {
            "capture_mode": "intercept-sdk",
            "method": "python-wrapper",
            "provider_name": "anthropic",
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            # requests.post("http://gateway.internal/v1/ingest", json=payload, timeout=1.0)
            pass
        except:
            pass

        return response
    return wrapped
