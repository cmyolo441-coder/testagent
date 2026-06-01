-- ASTRA Command OS — PostgreSQL Schema
-- Production database schema for persistent storage

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    goal TEXT NOT NULL,
    horizon TEXT DEFAULT '3m',
    agent_count INTEGER DEFAULT 1,
    verification_level INTEGER DEFAULT 2,
    status TEXT DEFAULT 'created',
    progress REAL DEFAULT 0.0,
    budget_limit DECIMAL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS objectives (
    id TEXT PRIMARY KEY,
    mission_id TEXT REFERENCES missions(id),
    parent_id TEXT REFERENCES objectives(id),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    objective_type TEXT DEFAULT 'task',
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    risk_level TEXT DEFAULT 'low',
    success_criteria TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    mission_id TEXT REFERENCES missions(id),
    objective_id TEXT REFERENCES objectives(id),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    risk_level TEXT DEFAULT 'low',
    assigned_agent TEXT,
    dependencies TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'general',
    model TEXT DEFAULT 'default',
    status TEXT DEFAULT 'idle',
    reputation REAL DEFAULT 0.5,
    missions_completed INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(id),
    task_id TEXT REFERENCES tasks(id),
    tool_name TEXT NOT NULL,
    arguments_json TEXT DEFAULT '{}',
    result_json TEXT DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    risk_score INTEGER DEFAULT 0,
    duration_ms REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL,
    action_description TEXT DEFAULT '',
    risk_score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    requested_by TEXT,
    approved_by TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    decided_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    context_json TEXT DEFAULT '{}',
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 0.5,
    source TEXT DEFAULT 'user',
    agent_id TEXT REFERENCES agents(id),
    mission_id TEXT REFERENCES missions(id),
    tags_json TEXT DEFAULT '[]',
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    claim_type TEXT DEFAULT 'factual',
    confidence REAL DEFAULT 0.5,
    verification_level INTEGER DEFAULT 0,
    status TEXT DEFAULT 'unverified',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_reports (
    id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(id),
    verification_level INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    confidence REAL DEFAULT 0.0,
    evidence_json TEXT DEFAULT '[]',
    assessor TEXT DEFAULT 'system',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    actor TEXT DEFAULT 'system',
    details TEXT DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW(),
    prev_hash TEXT,
    event_hash TEXT
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    mission_id TEXT REFERENCES missions(id),
    note TEXT NOT NULL,
    snapshot_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS costs (
    id SERIAL PRIMARY KEY,
    mission_id TEXT REFERENCES missions(id),
    provider TEXT,
    model TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_usd DECIMAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent ON tool_calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_memories_mission ON memories(mission_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
