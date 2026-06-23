# Token Tracker & AI FinOps Dashboard

Token Tracker is a corporate LLM Gateway and observability platform designed for comprehensive visibility and cost control across multiple AI providers. It features a Dual-Mode architecture: an active **Gateway Mode** (OpenAI-compatible proxy) and a passive **Intercept Mode** (SDK Sniffer).

## 📋 Table of Contents
- [Overview](#-overview)
- [Goal](#-goal)
- [Main Features](#-main-features)
- [Technologies](#-technologies)
- [Project Structure](#-project-structure)
- [How to Run](#-how-to-run)
- [How to Use](#-how-to-use)
- [Docker Support](#-docker-support)
- [Deployment](#-deployment)

## 🌟 Overview
As LLM usage scales, organizations often lose track of costs and productivity. Token Tracker provides a centralized dashboard to monitor token consumption, USD spend, and 'Actionable Output' metrics (Input/Output token ratios) in real-time.

## 🎯 Goal
To provide enterprise teams with a robust FinOps tool that enforces hard limits, redacts PII, and offers deep insights into AI adoption and productivity across departments.

## ✨ Main Features
- **Dual-Mode Observation:** Supports both proxying (Gateway) and non-intrusive interception (Intercept Mode).
- **FinOps Dashboard:** Real-time visualization of costs, model distribution, and user adoption.
- **Hard-Limit Enforcement:** Pre-request budget checks that block traffic when daily/monthly limits are exceeded.
- **Secure Key Vault:** AES-256-GCM encrypted storage for provider API keys.
- **Productivity Metrics:** Automatic calculation of 'Generation Ratio' to assess AI output efficiency.
- **Deduplication:** SHA256-based fingerprinting to prevent double-counting across gateway and intercept modes.

## 🛠️ Technologies
- **Backend:** Python 3.12, FastAPI, SQLAlchemy (TimescaleDB).
- **Frontend:** Angular 19, NGINX.
- **Persistence:** TimescaleDB (Time-series logs), Redis (Rate limiting).
- **Security:** AES-256-GCM Encryption.

## 📁 Project Structure
```text
token-tracker/
├── backend/            # FastAPI: Gateway proxy and management API
├── frontend/           # Angular: Observability dashboard
├── scripts/            # Infrastructure setup and database init
└── docker-compose.yml  # Full stack (App, DB, Redis, Grafana)
```

## 🚀 How to Run

### 1. Start Infrastructure
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd token-tracker/backend
pip install -r requirements.txt
uvicorn app.main:app
```

## 💡 How to Use
- **Gateway:** Point your OpenAI SDK to the Token Tracker URL.
- **Limits:** Configure daily and monthly budgets per user or department in the Admin panel.
- **Insights:** Use the dashboard to identify underutilized models or high-cost users.

## 🐳 Docker Support
Spin up the entire FinOps ecosystem including the time-series database:
```bash
docker-compose up --build
```

## 🚢 Deployment
Token Tracker is designed for production use behind a reverse proxy. It requires a persistent TimescaleDB instance for long-term log analysis and a Redis instance for real-time limit enforcement.
