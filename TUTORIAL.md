# Token Tracker Tutorial

This tutorial explains how to configure Claude CLI, Kiro, and Antigravity to automatically track all LLM usage with source identification.

> **Prerequisites:** Token Tracker must be running: `docker compose up -d` from the `token-tracker` directory.
> Dashboard: http://localhost:4200 | API: http://localhost:8000

---

## 1. Claude CLI (Always-On Tracking)

Claude CLI natively supports `ANTHROPIC_BASE_URL`. All requests route through the tracker with real token counts.

### PowerShell — Add to `$PROFILE` (auto-starts with every terminal)

```powershell
# Open your profile:
notepad $PROFILE

# Add these lines:
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:X_SOURCE = "claude-cli"
$env:X_PROJECT_ID = "00000000-0000-0000-0000-000000000000"
```

### Bash — Add to `~/.bashrc` or `~/.zshrc`

```bash
export ANTHROPIC_BASE_URL="http://localhost:8000"
export X_SOURCE="claude-cli"
export X_PROJECT_ID="00000000-0000-0000-0000-000000000000"
```

After saving, every new terminal session will automatically route Claude CLI through the tracker. The `X-Source: claude-cli` header tells the tracker which IDE originated the request.

---

## 2. Kiro IDE (Always-On Tracking)

Kiro uses AWS-managed endpoints, so `ANTHROPIC_BASE_URL` doesn't apply. Use the **agent hook** for automatic tracking.

### Setup: Copy the hook to your workspace

The hook file is at `.kiro/hooks/track-kiro-usage.kiro.hook`. It fires on every `agentStop` event and reports to the tracker with `source_type: "kiro"`.

It works automatically in any workspace that has the hook file. The tracker identifies this traffic as coming from Kiro.

### How it works

Every time Kiro's agent finishes a response, the hook sends:
```json
{
  "source_type": "kiro",
  "provider_name": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "capture_mode": "intercept",
  "input_tokens": 2000,
  "output_tokens": 1000
}
```

### For accurate token counts: MITM Proxy

```powershell
# Install mitmproxy (one-time)
pip install mitmproxy requests

# Add to $PROFILE for always-on:
function Start-Kiro {
    Start-Process powershell -ArgumentList "-Command", "mitmdump --listen-port 9090 -s '$PWD\backend\app\services\intercept_mitm.py' --set block_global=false" -WindowStyle Minimized
    Start-Sleep 2
    $env:HTTP_PROXY = "http://localhost:9090"
    $env:HTTPS_PROXY = "http://localhost:9090"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Kiro\Kiro.exe"
}
Set-Alias kiro Start-Kiro
```

The MITM proxy detects Kiro from the user-agent and tags it as `source_type: "kiro"`.

---

## 3. Antigravity / Cursor (Always-On Tracking)

Antigravity supports setting a custom base URL for LLM calls.

### PowerShell — Add to `$PROFILE`

```powershell
# Add to $PROFILE for always-on:
function Start-Antigravity {
    $env:ANTHROPIC_BASE_URL = "http://localhost:8000"
    $env:OPENAI_BASE_URL = "http://localhost:8000/v1"
    $env:X_SOURCE = "antigravity"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe"
}
Set-Alias ag Start-Antigravity
```

### Alternative: IDE Settings

1. Open Settings (`Ctrl+,`)
2. Search for "Base URL"
3. Set Anthropic base URL to `http://localhost:8000`
4. Set OpenAI base URL to `http://localhost:8000/v1`

The tracker detects the source from the `X-Source` header or user-agent.

---

## 4. Source Identification

The tracker automatically identifies which AI IDE sent each request using:

| Priority | Method | Example |
|----------|--------|---------|
| 1 | `X-Source` header | `X-Source: claude-cli` |
| 2 | User-Agent detection | `kiro`, `antigravity`, `cursor` in UA |
| 3 | Ingest payload | `source_type` field in `/v1/ingest` body |

The dashboard shows a breakdown by source in the stats API:
```json
{
  "total_spend": 0.045,
  "total_tokens": 9000,
  "by_source": [
    {"source_type": "kiro", "count": 5, "cost": 0.025, "tokens": 5000},
    {"source_type": "claude-cli", "count": 3, "cost": 0.015, "tokens": 3000},
    {"source_type": "antigravity", "count": 1, "cost": 0.005, "tokens": 1000}
  ]
}
```

---

## 5. Setting Hard Limits

1. Open the Dashboard at `http://localhost:4200`
2. Navigate to **Hard Limits**
3. Enter values for **Daily**, **Monthly**, or **Total** limits (in USD)
4. Click **Activate Hard Limits**
5. When a request exceeds the limit, the tracker returns a 429 error and blocks it

---

## 6. All-in-One PowerShell Profile

Add this complete block to your `$PROFILE` for always-on tracking across all tools:

```powershell
# === Token Tracker: Always-On LLM Tracking ===

# Claude CLI: Direct gateway (no proxy needed, uses base URL)
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:X_SOURCE = "claude-cli"
$env:X_PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# Antigravity launcher with tracking
function Start-Antigravity {
    $env:ANTHROPIC_BASE_URL = "http://localhost:8000"
    $env:OPENAI_BASE_URL = "http://localhost:8000/v1"
    $env:X_SOURCE = "antigravity"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Antigravity\Antigravity.exe"
    # Clean up proxy vars after launch so git/npm aren't affected
    Remove-Item env:NODE_TLS_REJECT_UNAUTHORIZED -ErrorAction SilentlyContinue
}
Set-Alias ag Start-Antigravity

# Kiro launcher with MITM proxy (requires: pip install mitmproxy)
# The proxy ONLY intercepts LLM API domains (anthropic, google, bedrock)
# All other traffic (git, npm, browser) passes through unmodified
function Start-Kiro {
    $env:HTTP_PROXY = "http://localhost:9090"
    $env:HTTPS_PROXY = "http://localhost:9090"
    $env:NO_PROXY = "localhost,127.0.0.1,github.com,*.github.com,registry.npmjs.org,*.npmjs.org"
    $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
    & "$env:LOCALAPPDATA\Programs\Kiro\Kiro.exe"
    # Clean up proxy vars so they don't leak to other commands
    Remove-Item env:HTTP_PROXY -ErrorAction SilentlyContinue
    Remove-Item env:HTTPS_PROXY -ErrorAction SilentlyContinue
    Remove-Item env:NO_PROXY -ErrorAction SilentlyContinue
    Remove-Item env:NODE_TLS_REJECT_UNAUTHORIZED -ErrorAction SilentlyContinue
}
Set-Alias kiro Start-Kiro

# Auto-start token tracker (if not running)
function Ensure-TokenTracker {
    $running = docker compose -f "$HOME\workspace\sandbox\poc-repository\token-tracker\docker-compose.yml" ps --status running 2>$null
    if (-not $running -or $running -notmatch "backend") {
        docker compose -f "$HOME\workspace\sandbox\poc-repository\token-tracker\docker-compose.yml" up -d
    }
}
Ensure-TokenTracker
```

> **Important:** The proxy is ONLY set inside the launcher functions and cleaned up after the IDE starts. Git, npm, and other tools are never affected. The MITM proxy uses `--allow-hosts` to only intercept LLM API domains — everything else passes through untouched.

---

## 7. Verifying It Works

```powershell
# Check stats
Invoke-RestMethod http://localhost:8000/v1/logs/stats/00000000-0000-0000-0000-000000000000

# Check recent logs
Invoke-RestMethod http://localhost:8000/v1/logs/00000000-0000-0000-0000-000000000000?limit=5
```

Open the dashboard at http://localhost:4200 to see metrics by source.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Metrics are zero | Verify `$env:ANTHROPIC_BASE_URL` is set: `echo $env:ANTHROPIC_BASE_URL` |
| Kiro not tracked | Ensure the `.kiro/hooks/track-kiro-usage.kiro.hook` file exists in workspace |
| Source shows "api" | Add `$env:X_SOURCE = "your-tool"` before launching |
| 429 errors | Check Hard Limits in dashboard — may have hit budget |
| Backend not starting | Run `docker compose logs backend` to diagnose |
| MITM cert errors | Install mitmproxy CA: `http://mitm.it` while proxy runs |
