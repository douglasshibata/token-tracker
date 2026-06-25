# Token Tracker (Backend)

A high-performance LLM FinOps Observability platform that tracks costs, token usage, and productivity metrics across various AI providers.

## 🛠️ Technical Stack & Versions
- **Python**: 3.12 (Slim)
- **Framework**: FastAPI 0.115.8
- **Database**: PostgreSQL (TimescaleDB), Redis
- **ORM**: SQLAlchemy 2.0.38
- **Data Analysis**: Pandas 2.2.3
- **Testing**: Pytest 8.3.4

## 🚀 Local Setup
1. **Prerequisites**: Python 3.12+, PostgreSQL, Redis.
2. **Environment**:
   ```bash
   cd backend
   cp .env.example .env
   # Configure DB and Provider settings
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 How to Use
- **Start the Server**: `./entrypoint.sh`
- **Database Migration**: `python scripts/init_db.py`
- **Testing**: `PYTHONPATH=. pytest tests/`

## 🚢 Deployment
- **Docker**:
  ```bash
  docker build -t token-tracker-backend .
  ```
- **Docker Compose**: Use the root `docker-compose.yml` to orchestrate backend, frontend, and databases.

## ⚙️ Environment Variables
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis connection string.
- `VAULT_SECRET_KEY`: 32-byte key for AES-256 encryption.

## 🤝 Development Guidelines
- Maintain high test coverage for FinOps logic.
- Use `black` and `isort` for code formatting.
- Log all API interactions for deduplication and auditing.
