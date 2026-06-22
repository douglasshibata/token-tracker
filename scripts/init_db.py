import asyncio
import asyncpg
import os

SCHEMA = """
-- Projects/Campaigns with Hard Limits
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    daily_limit DECIMAL(10,2),
    monthly_limit DECIMAL(10,2),
    total_limit DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- AI Sessions for tracking session-based productivity
CREATE TABLE IF NOT EXISTS ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    source VARCHAR(50), -- 'claude-cli', 'antigravity', 'kiro'
    started_at TIMESTAMP DEFAULT NOW()
);

-- API Logs including blocking and productivity information
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    session_id UUID REFERENCES ai_sessions(id),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    was_blocked BOOLEAN DEFAULT FALSE,
    block_reason TEXT,
    is_tool_call BOOLEAN DEFAULT FALSE,
    tool_name VARCHAR(100),
    generation_ratio DECIMAL(10, 2), -- (output / input) * 100
    request_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

HYPERTABLE_SQL = "SELECT create_hypertable('api_logs', 'created_at', if_not_exists => TRUE);"

async def init_db():
    conn_str = os.getenv("DATABASE_URL", "postgresql://tracker:password@localhost:5432/token_tracker")
    try:
        conn = await asyncpg.connect(conn_str)
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        await conn.execute(SCHEMA)

        # Insert default project to avoid FK errors
        await conn.execute("""
            INSERT INTO projects (id, name, description)
            VALUES ('00000000-0000-0000-0000-000000000000', 'Default Project', 'Auto-generated default project')
            ON CONFLICT (id) DO NOTHING
        """)

        try:
            await conn.execute(HYPERTABLE_SQL)
        except Exception as e:
            print(f"Warning: Could not create hypertable: {e}")

        print("Database initialized successfully.")
        await conn.close()
    except Exception as e:
        print(f"Skipping DB connection in init script: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
