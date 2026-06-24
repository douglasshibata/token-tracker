# Token Tracker - MITM Proxy Interceptor for Kiro & Antigravity
# Only intercepts LLM API domains. All other traffic passes through untouched.
#
# Prerequisites:
#   pip install mitmproxy requests
#
# Usage:
#   .\start-intercept.ps1           # Start the proxy on port 9090
#   .\start-intercept.ps1 -Port 8080  # Custom port

param(
    [int]$Port = 9090
)

$scriptPath = Join-Path $PSScriptRoot "backend\app\services\intercept_mitm.py"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Token Tracker - MITM Intercept Proxy" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proxy port: $Port" -ForegroundColor Yellow
Write-Host "Tracker:    http://localhost:8000" -ForegroundColor Yellow
Write-Host "Dashboard:  http://localhost:4200" -ForegroundColor Yellow
Write-Host ""
Write-Host "ONLY intercepts LLM domains:" -ForegroundColor Green
Write-Host "  - api.anthropic.com"
Write-Host "  - generativelanguage.googleapis.com"
Write-Host "  - bedrock-runtime.*.amazonaws.com"
Write-Host ""
Write-Host "All other traffic (git, npm, etc.) passes through unmodified." -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

# --ignore-hosts: regex of domains to NOT intercept (pass through as-is)
# We use --allow-hosts to ONLY intercept LLM domains
mitmdump --listen-port $Port -s $scriptPath --set block_global=false --allow-hosts "^(api\.anthropic\.com|generativelanguage\.googleapis\.com|.*bedrock-runtime.*\.amazonaws\.com|.*q\.us-east-1\.amazonaws\.com)$"
