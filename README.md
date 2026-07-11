# Token Tracker & AI FinOps Dashboard

Token Tracker is a corporate LLM Gateway and observability platform designed for comprehensive visibility and cost control across multiple AI providers. It features a Dual-Mode architecture: an active **Gateway Mode** (proxy) and a passive **Intercept Mode** (MITM/Hook).

## 📋 Table of Contents
- [Overview](#-overview)
- [Quick Start](#-quick-start)
- [Integrations](#-integrations)
- [Main Features](#-main-features)
- [Technologies](#-technologies)
- [Project Structure](#-project-structure)
- [Security](#security)
- [Deployment](#-deployment)
- [License](#license)

## 🌟 Overview
As LLM usage scales, organizations often lose track of costs and productivity. Token Tracker provides a centralized dashboard to monitor token consumption, USD spend, and 'Actionable Output' metrics (Input/Output token ratios) in real-time.

## 🚀 Quick Start

```powershell
# 1. Start the full stack
cd token-tracker
docker compose up --build -d

# 2. Open the dashboard
Start-Process "http://localhost:4200"
```

Services:
| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:4200 | Frontend metrics UI |
| Backend API | http://localhost:8000 | Gateway + Ingest API |
| TimescaleDB | localhost:5432 | Persistent storage |
| Redis | localhost:6379 | Rate limiting |

## 🔌 Integrations

### Claude CLI (Direct Gateway)
Claude CLI natively supports `ANTHROPIC_BASE_URL`. All requests route through the tracker with real token counts.

**PowerShell (add to `$PROFILE`):**
```powershell
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:X_PROJECT_ID = "00000000-0000-0000-0000-000000000000"
$env:X_SOURCE = "claude-cli"
```

### Kiro IDE
Supports Agent Hooks or MITM Proxy.
(See detailed instructions in original documentation).

### Antigravity / Cursor
Supports Environment Variables or IDE Settings for custom Base URLs.

---

## ✨ Main Features
- **Dual-Mode Observation:** Supports both proxying (Gateway) and non-intrusive interception (Hooks + MITM).
- **FinOps Dashboard:** Real-time visualization of costs, model distribution, and user adoption.
- **Hard-Limit Enforcement:** Pre-request budget checks that block traffic.
- **Productivity Metrics:** Automatic calculation of 'Generation Ratio'.

## 🛠️ Technologies
- **Languages**: Node.js 20+, Python 3.12, Go 1.24.
- **Backend:** Python FastAPI, asyncpg (TimescaleDB).
- **Frontend:** Angular 19+, Signals.
- **Persistence:** TimescaleDB, Redis.

## 📁 Project Structure
- `backend/`: FastAPI Gateway proxy + Ingest API.
- `frontend/`: Angular Observability dashboard.
- `logq/`: Go CLI for high-performance log querying.

## Security
- **Credential Safety**: Provider API keys are handled via environment variables or secure vaulting.
- **Data Privacy**: PII stripping available at the gateway level.
- **TLS**: Supports termination for secure proxying.

## 🚢 Deployment
Requires a persistent TimescaleDB instance and Redis for real-time limit enforcement.

## License
MIT License

---

## 🛠️ Project Deep Dive & Technical Guide

### 🎯 Main Purpose
AI FinOps & Observability platform tracking token consumption, model costs, and billing thresholds.

### 🧰 Tecnologias Utilizadas (Tech Stack)
- **Primary Technologies:** Angular 19.2.2, Docker / Docker Compose, FastAPI, Go 1.24.3, Node.js / npm, Python 3.12
- **Deployment Strategy:** Container-ready with standard Docker/Docker Compose integrations where applicable.

### 🚀 Como Implantar e Executar (How to Deploy & Run)
#### Frontend (Angular / Node.js)
1. Navigate to the frontend directory.
2. Install dependencies: `npm install`.
3. Run development server: `npm start` or `npm run dev`.

#### Python Engine / FastAPI
1. Install dependencies: `pip install -r requirements.txt`.
2. Run the server/script: `uvicorn main:app --reload` or `python main.py`.

#### Go CLI / Service
1. Build the module: `go build`.
2. Execute: `./token-tracker` (or project executable name).

---
