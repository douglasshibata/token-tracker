# Dual-Mode LLM Tracker & Interceptor

A unified corporate observability platform for tracking and limiting LLM usage through two modes:

## 1. Gateway Mode (Active Control)
Applications explicitly route through the gateway.
- **Base URL:** `http://localhost:8000/v1`
- **Supported:** OpenAI-compatible tools (Cursor, Python SDK, etc.)
- **Features:** Budget enforcement (429 blocking), centralized keys.

## 2. Intercept Mode (Passive Visibility)
Transparently captures direct traffic to providers.
- **Sub-mode A (MITM):** Uses `mitmproxy` to decrypt and parse network traffic.
- **Sub-mode B (SDK Wrapper):** Code-level monkeypatching of LLM libraries.
- **Sub-mode C (Mirror):** Read-only packet sniffing for discovery.
- **`logq` CLI Tool:** High-performance Go-based log analyzer for deep-diving into `.jsonl` traffic.

## 🛠️ Setup Guide

### Gateway Integration (Example: Python)
```python
import openai
client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="gw-any-key" # Gateway manages provider keys
)
```

### MITM Intercept Setup
1. Deploy `intercept_mitm.py` as a mitmproxy addon.
2. Install the generated CA certificate on target machines.
3. Set `HTTP_PROXY="http://localhost:8080"`.

## 🚀 Deployment
```bash
docker-compose up -d
```
The database will automatically initialize a default project and admin user.
