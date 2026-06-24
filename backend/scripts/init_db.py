import asyncio
import asyncpg
import os

SCHEMA = """
-- Unified Corporate LLM Gateway & Intercept Schema

-- Projects
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

-- Providers
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    base_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vaulted Keys (Gateway Mode)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES providers(id),
    encrypted_key TEXT NOT NULL,
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Corporate Users
CREATE TABLE IF NOT EXISTS gateway_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user',
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unified Request Logs (api_logs)
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    capture_mode VARCHAR(30) NOT NULL, -- 'gateway', 'intercept-mitm', 'intercept-sdk', 'intercept-mirror'
    method VARCHAR(20),               -- 'proxy', 'mitm'
    source_type VARCHAR(50),          -- 'claude-cli', 'kiro', 'antigravity', 'cursor', 'api'
    was_enforceable BOOLEAN DEFAULT TRUE,
    was_blocked BOOLEAN DEFAULT FALSE,

    user_id UUID REFERENCES gateway_users(id),
    provider_id UUID REFERENCES providers(id),

    model VARCHAR(100),
    request_messages JSONB,
    status VARCHAR(20),

    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cost DECIMAL(10,6) DEFAULT 0.0,
    generation_ratio DECIMAL(10,4),
    is_tool_call BOOLEAN DEFAULT FALSE,
    tool_name VARCHAR(100),

    latency_ms INT,
    source_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

-- IP to User mapping for Intercept mode
CREATE TABLE IF NOT EXISTS ip_user_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL,
    user_id UUID REFERENCES gateway_users(id),
    department VARCHAR(100),
    device_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ip_address, is_active)
);

-- Deduplication tracking
CREATE TABLE IF NOT EXISTS request_fingerprints (
    fingerprint VARCHAR(64) PRIMARY KEY, -- SHA256 of (timestamp+model+input_tokens+ip)
    request_id UUID REFERENCES api_logs(id),
    capture_mode VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Discovery log (for finding unknown LLM endpoints)
CREATE TABLE IF NOT EXISTS endpoint_discovery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255),
    ip_address VARCHAR(45),
    path_pattern VARCHAR(500),
    request_count INT DEFAULT 1,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    is_llm_related BOOLEAN DEFAULT NULL, -- NULL = unreviewed
    notes TEXT
);

-- Budgets (Legacy/Entity based - optional)
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(20), -- 'company', 'department', 'user'
    entity_id VARCHAR(255),
    cost_limit DECIMAL(10,2),
    cost_used DECIMAL(10,2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_logs_mode ON api_logs(capture_mode, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_project ON api_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_ip_mapping_lookup ON ip_user_mapping(ip_address) WHERE is_active;
"""

async def init_db():
    conn_str = os.getenv("DATABASE_URL", "postgresql://tracker:password@localhost:5432/token_tracker")
    try:
        conn = await asyncpg.connect(conn_str)
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        await conn.execute(SCHEMA)

        # Seed defaults
        await conn.execute("""
            INSERT INTO projects (id, name, description)
            VALUES ('00000000-0000-0000-0000-000000000000', 'Default Project', 'Auto-created default project')
            ON CONFLICT DO NOTHING;

            INSERT INTO gateway_users (id, display_name, email, role)
            VALUES ('00000000-0000-0000-0000-000000000000', 'System Admin', 'admin@company.com', 'admin')
            ON CONFLICT DO NOTHING;

            INSERT INTO providers (name, base_url) VALUES
            ('claude', 'https://api.anthropic.com'),
            ('google', 'https://generativelanguage.googleapis.com')
            ON CONFLICT DO NOTHING;
        """)

        print("Dual-Mode Database initialized.")
        await conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
