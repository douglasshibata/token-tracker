# Dual-Mode LLM Tracker & Interceptor

A comprehensive corporate observability platform for tracking and limiting LLM usage across the entire organization. It supports both explicit **Gateway (Proxy)** and passive **Interception (MITM)** modes.

## 🚀 Dual-Mode Architecture

### 1. Gateway Mode (Active Control)
Applications route through the Gateway as their primary LLM endpoint (`http://localhost:8000/v1`).
- **Centralized Key Management:** Users never see provider API keys.
- **Budget Enforcement:** Hard-blocking (429 errors) when limits are exceeded.
- **Dynamic Routing:** Alias-based routing to different models/providers.

### 2. Intercept Mode (Passive Visibility)
Captures direct traffic from unconfigured tools (Browser, CLI) using a network middleman.
- **Sub-mode A (MITM):** Uses `mitmproxy` to decrypt and parse traffic.
- **Sub-mode B (SDK Wrapper):** Code-level monkeypatching of libraries.
- **Sub-mode C (Mirror):** Read-only packet sniffing for provider discovery.

## 🛠️ Unified Data Pipeline
All traffic flows through a common pipeline that:
- Normalizes requests/responses from Anthropic, Gemini, etc.
- Calculates costs in real-time.
- Updates hierarchical budgets (Company -> Dept -> User).
- Logs time-series data to TimescaleDB.

## 📁 Project Structure

```
token-tracker/
├── backend/            # FastAPI Proxy & Management API
├── frontend/           # Angular 19 Dashboard
├── scripts/            # Database initialization & maintenance
└── docker-compose.yml  # Full stack orchestration
```

## 💻 How to Run

### 1. Configure Environment
Copy `backend/.env.example` to `backend/.env` and add your API keys.

### 2. Start the Stack
```bash
docker-compose up -d
```

### 3. Access Dashboard
Open `http://localhost:4200` to view analytics, set limits, and export reports.

## 📊 Analytics & Reporting
- **Productivity Metrics:** Automatic calculation of "Generation Ratio" and tool-use efficiency.
- **Export Engine:** Download monthly CSV/Excel summaries or save beautiful PDF reports directly from the browser.
