# Token Tracker & Request Interceptor

A comprehensive system to track LLM token usage and enforce hard budget limits across multiple AI tools and providers.

## Architecture

- **Backend Proxy (FastAPI):** Intercepts API requests, performs token estimation, enforces budgets, and logs productivity metrics.
- **Database (TimescaleDB/PostgreSQL):** Stores time-series data of API calls, sessions, and budget configurations.
- **Frontend Dashboard (Angular):** Visualizes spending, productivity (Generation Ratio), and allows setting hard limits.
- **Docker Orchestration:** Simple deployment using `docker-compose`.

## Features

- **Hard Blocking:** Automatically stops requests with a 429 error if daily, monthly, or total limits are exceeded.
- **Productivity Tracking:** Calculates "Generation Ratio" (Output/Input) and detects tool/code generation calls.
- **Multi-Tool Support:** Intercepts Claude Code CLI, Antigravity IDE, and Kiro IDE.
- **Multi-Provider support:** Handles Anthropic, Gemini, and Antigravity APIs.

## Installation

1.  **Clone the repository.**
2.  **Configure environment variables:**
    Copy `backend/.env.example` to `backend/.env` and fill in your API keys.
3.  **Start the stack:**
    ```bash
    docker-compose up -d --build
    ```
4.  **Initialize the Database:**
    The system auto-initializes a default project on startup.

## Usage

See [TUTORIAL.md](./TUTORIAL.md) for detailed instructions on how to point your AI tools to the tracker.
