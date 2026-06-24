# Token Tracker - MITM Proxy Interceptor for Kiro & Antigravity
# This script starts mitmproxy to capture LLM API calls and report them to the tracker.
#
# Prerequisites:
#   pip install mitmproxy requests
#
# After first run, install the mitmproxy CA certificate:
#   1. Open http://mitm.it in browser while proxy is running
#   2. Download and install the certificate for Windows
#   OR: Import from ~/.mitmproxy/mitmproxy-ca-cert.cer
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
Write-Host "To use with Kiro/Antigravity, set these env vars BEFORE launching:" -ForegroundColor Green
Write-Host ""
Write-Host '  $env:HTTP_PROXY = "http://localhost:' + $Port + '"'
Write-Host '  $env:HTTPS_PROXY = "http://localhost:' + $Port + '"'
Write-Host '  $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"'
Write-Host ""
Write-Host "Then launch the IDE from the same terminal." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

mitmdump --listen-port $Port -s $scriptPath --set block_global=false
