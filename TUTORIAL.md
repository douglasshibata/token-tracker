# Token Tracker Tutorial

This tutorial explains how to configure your development environment to track costs and enforce limits.

## 1. Intercepting Claude Code CLI

Claude CLI uses the `ANTHROPIC_BASE_URL` environment variable to determine where to send requests.

```bash
# Point to your local tracker
export ANTHROPIC_BASE_URL="http://localhost:8000"

# Tag your requests (Optional)
export X_PROJECT_ID="00000000-0000-0000-0000-000000000000"
export X_SOURCE="claude-cli"

# Run Claude as usual
claude "Write a python script"
```

## 2. Intercepting Kiro IDE (AWS Q)

Kiro often respects system proxy settings. Launch it from the terminal to ensure it inherits the variables:

```bash
export HTTP_PROXY="http://localhost:8000"
export HTTPS_PROXY="http://localhost:8000"
export NODE_TLS_REJECT_UNAUTHORIZED=0

# Launch Kiro
/Applications/Kiro.app/Contents/MacOS/Kiro &
```

## 3. Intercepting Antigravity / Cursor

Most IDEs based on VS Code allow setting a custom API base URL in their settings:

1.  Open Settings (Cmd+,).
2.  Search for "Base URL".
3.  Set the endpoint to `http://localhost:8000/v1`.

## 4. Setting Hard Limits

1.  Open the Dashboard at `http://localhost:4200`.
2.  Navigate to **Hard Limits**.
3.  Enter values for **Daily**, **Monthly**, or **Total** limits.
4.  Click **Activate Hard Limits**.
5.  If an AI request exceeds these limits, you will receive a 429 error, and the request will be blocked.

## 5. Analyzing Productivity

Navigate to the **Productivity** tab to see:
- **Generation Ratio:** Are you getting enough code back for the context you provide?
- **Actionable Output:** How often is the AI actually using tools vs. just chatting?
- **Top Actions:** Which tools (Write, Bash, etc.) are used most often.
