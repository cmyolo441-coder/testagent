-- ASTRA Command OS — SQLite Schema
-- Local-first storage for offline mode

CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    horizon TEXT DEFAULT '3m',
    agent_count INTEGER DEFAULT 1,
    verification_level INTEGER DEFAULT 2,
    status TEXT DEFAULT 'created',
    progress REAL DEFAULT 0.0,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    risk_level TEXT DEFAULT 'low',
    assigned_agent TEXT,
    dependencies TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'general',
    status TEXT DEFAULT 'idle',
    reputation REAL DEFAULT 0.5,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    context_json TEXT DEFAULT '{}',
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 0.5,
    source TEXT DEFAULT 'user',
    mission_id TEXT,
    tags_json TEXT DEFAULT '[]',
    access_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    actor TEXT DEFAULT 'system',
    details TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL,
    prev_hash TEXT,
    event_hash TEXT
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    note TEXT NOT NULL,
    snapshot_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id);
CREATE INDEX IF NOT EXISTS idx_memories_mission ON memories(mission_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
