# Token Tracker & AI FinOps Dashboard

Token Tracker is a corporate LLM Gateway and observability platform designed for comprehensive visibility and cost control across multiple AI providers. It features a Dual-Mode architecture: an active **Gateway Mode** (proxy) and a passive **Intercept Mode** (MITM/Hook).

## 📋 Table of Contents
- [Overview](#-overview)
- [Quick Start](#-quick-start)
- [Integrations](#-integrations)
- [Main Features](#-main-features)
- [Technologies](#-technologies)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)

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

**PowerShell (add to `$PROFILE` for always-on tracking):**

```powershell
# Add these lines to your PowerShell profile:
# notepad $PROFILE

$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:X_PROJECT_ID = "00000000-0000-0000-0000-000000000000"
$env:X_SOURCE = "claude-cli"
```

**Bash (add to `~/.bashrc` or `~/.zshrc`):**

```bash
export ANTHROPIC_BASE_URL="http://localhost:8000"
export X_PROJECT_ID="00000000-0000-0000-0000-000000000000"
export X_SOURCE="claude-cli"
```

After adding to your profile, all Claude CLI sessions are automatically tracked.

---

### Kiro IDE

Kiro routes through AWS-managed endpoints, so `ANTHROPIC_BASE_URL` doesn't work. Two approaches:

#### Option A: Agent Hook (Automatic, estimated tokens)

Copy the `.kiro/hooks/` directory to your workspace. The `track-kiro-usage` hook fires on every `agentStop` event and reports usage to the tracker automatically.

```json
{
  "name": "Track Kiro Usage",
  "version": "1.0.0",
  "when": { "type": "agentStop" },
  "then": {
    "type": "runCommand",
    "command": "powershell -Command \"try { $body = @{provider_name='anthropic';model='claude-sonnet-4-20250514';capture_mode='intercept';source_ip='127.0.0.1';project_id='00000000-0000-0000-0000-000000000000';input_tokens=2000;output_tokens=1000;latency_ms=3000;method='kiro-agent';is_tool_call=$true;tool_name='kiro-agent-stop';status='success'} | ConvertTo-Json; Invoke-RestMethod -Uri 'http://localhost:8000/v1/ingest' -Method Post -Body $body -ContentType 'application/json' | Out-Null; Write-Output 'Tracked' } catch { Write-Output 'Track failed' }\""
  }
}
```

#### Option B: MITM Proxy (Accurate, real token counts)

```powershell
# Install mitmproxy (one-time)
pip install mitmproxy requests

# Start the intercept proxy
.\start-intercept.ps1

# In a NEW terminal, launch Kiro with proxy settings
$env:HTTP_PROXY = "http://localhost:9090"
$env:HTTPS_PROXY = "http://localhost:9090"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
& "$env:LOCALAPPDATA\Programs\Kiro\Kiro.exe"
```

**To always start with proxy (add to `$PROFILE`):**

```powershell
function Start-Kiro {
    $env:HTTP_PROXY = "http://localhost:9090"
    $env:HTTPS_PROXY = "http://localhost:9090"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Kiro\Kiro.exe"
}
Set-Alias kiro Start-Kiro
```

---

### Antigravity / Cursor

VS Code-based IDEs that support custom base URLs.

#### Option A: Environment Variables (add to `$PROFILE` for always-on)

```powershell
# Add to $PROFILE for permanent tracking:
function Start-Antigravity {
    $env:ANTHROPIC_BASE_URL = "http://localhost:8000"
    $env:OPENAI_BASE_URL = "http://localhost:8000/v1"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe"
}
Set-Alias ag Start-Antigravity
```

#### Option B: IDE Settings

1. Open Settings (`Ctrl+,`)
2. Search for "Base URL" or "API Base"
3. Set to `http://localhost:8000/v1`

#### Option C: MITM Proxy (same as Kiro)

```powershell
# Start interceptor first
.\start-intercept.ps1

# Launch with proxy
$env:HTTP_PROXY = "http://localhost:9090"
$env:HTTPS_PROXY = "http://localhost:9090"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
& "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe"
```

---

### All-in-One Launcher

Create a single script to start everything with tracking enabled:

```powershell
# Save as: Start-TrackedDev.ps1
# Starts token tracker + launches your IDE with tracking enabled

# 1. Ensure tracker is running
docker compose up -d

# 2. Start MITM proxy in background (if installed)
$mitmJob = Start-Job { mitmdump --listen-port 9090 -s "backend\app\services\intercept_mitm.py" --set block_global=false }

# 3. Set env vars
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:HTTP_PROXY = "http://localhost:9090"
$env:HTTPS_PROXY = "http://localhost:9090"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"

Write-Host "Token Tracker ready! Dashboard: http://localhost:4200" -ForegroundColor Green
```

## ✨ Main Features
- **Dual-Mode Observation:** Supports both proxying (Gateway) and non-intrusive interception (Hooks + MITM).
- **FinOps Dashboard:** Real-time visualization of costs, model distribution, and user adoption.
- **Hard-Limit Enforcement:** Pre-request budget checks that block traffic when daily/monthly limits are exceeded.
- **Productivity Metrics:** Automatic calculation of 'Generation Ratio' to assess AI output efficiency.
- **Deduplication:** SHA256-based fingerprinting to prevent double-counting across gateway and intercept modes.
- **Multi-IDE Support:** Works with Claude CLI, Kiro, Antigravity, and Cursor.

## 🛠️ Technologies
- **Backend:** Python 3.12, FastAPI, asyncpg (TimescaleDB).
- **Frontend:** Angular 19, NGINX.
- **Persistence:** TimescaleDB (Time-series logs), Redis (Rate limiting).
- **Intercept:** mitmproxy (optional, for accurate MITM tracking).

## 📁 Project Structure
```text
token-tracker/
├── backend/                    # FastAPI: Gateway proxy + Ingest API
│   └── app/services/
│       └── intercept_mitm.py   # mitmproxy addon script
├── frontend/                   # Angular: Observability dashboard
├── logq/                       # Go CLI: Log query tool
├── start-intercept.ps1         # PowerShell: Start MITM proxy
├── docker-compose.yml          # Full stack orchestration
└── TUTORIAL.md                 # Step-by-step integration guide
```

## 🚢 Deployment
Token Tracker is designed for production use behind a reverse proxy. It requires a persistent TimescaleDB instance for long-term log analysis and a Redis instance for real-time limit enforcement.

For always-on tracking in development, add the environment variables and launcher functions to your shell profile (`$PROFILE` on PowerShell, `~/.bashrc` on Linux/macOS).
