"""PostgreSQL Memory Store — Production-grade persistent memory"""
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSycopg2 = True
except ImportError:
    HAS_PSycopg2 = False

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


class PostgresMemoryStore:
    """PostgreSQL-backed persistent memory store for production deployments."""

    def __init__(self, dsn: str = None, host: str = "localhost", port: int = 5432,
                 database: str = "astra_memory", user: str = "astra", password: str = ""):
        if not HAS_PSycopg2:
            raise ImportError("psycopg2 is required: pip install psycopg2-binary")

        self.dsn = dsn or f"host={host} port={port} dbname={database} user={user} password={password}"
        self._init_db()

    def _get_conn(self):
        return psycopg2.connect(self.dsn, cursor_factory=psycopg2.extras.RealDictCursor)

    @contextmanager
    def _connection(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        memory_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        context_json JSONB DEFAULT '{}',
                        importance REAL DEFAULT 0.5,
                        confidence REAL DEFAULT 0.5,
                        source TEXT DEFAULT 'user',
                        agent_id TEXT,
                        mission_id TEXT,
                        task_id TEXT,
                        tags_json JSONB DEFAULT '[]',
                        access_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMPTZ,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        expires_at TIMESTAMPTZ,
                        metadata_json JSONB DEFAULT '{}'
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memory_edges (
                        id SERIAL PRIMARY KEY,
                        source_id TEXT NOT NULL REFERENCES memories(id),
                        target_id TEXT NOT NULL REFERENCES memories(id),
                        relation TEXT NOT NULL,
                        weight REAL DEFAULT 1.0,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_mission ON memories(mission_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC)")

    def store(self, record) -> str:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories
                    (id, memory_type, content, context_json, importance, confidence, source,
                     agent_id, mission_id, task_id, tags_json, access_count, last_accessed,
                     created_at, updated_at, expires_at, metadata_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        context_json = EXCLUDED.context_json,
                        importance = EXCLUDED.importance,
                        confidence = EXCLUDED.confidence,
                        tags_json = EXCLUDED.tags_json,
                        updated_at = EXCLUDED.updated_at,
                        metadata_json = EXCLUDED.metadata_json
                """, (
                    record.id, record.memory_type, record.content,
                    json.dumps(record.context), record.importance, record.confidence,
                    record.source, record.agent_id, record.mission_id, record.task_id,
                    json.dumps(record.tags), record.access_count, record.last_accessed,
                    record.created_at, record.updated_at, record.expires_at,
                    json.dumps(record.metadata),
                ))
        return record.id

    def retrieve(self, memory_id: str):
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM memories WHERE id = %s", (memory_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_record(row)

    def search(self, query: str = None, memory_type: str = None,
               mission_id: str = None, tags: list[str] = None,
               min_importance: float = 0.0, limit: int = 20):
        conditions = ["1=1"]
        params = []

        if query:
            conditions.append("content ILIKE %s")
            params.append(f"%{query}%")
        if memory_type:
            conditions.append("memory_type = %s")
            params.append(memory_type)
        if mission_id:
            conditions.append("mission_id = %s")
            params.append(mission_id)
        if min_importance > 0:
            conditions.append("importance >= %s")
            params.append(min_importance)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM memories WHERE {where} ORDER BY importance DESC, created_at DESC LIMIT %s"
        params.append(limit)

        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [self._row_to_record(r) for r in rows]

    def update_access(self, memory_id: str):
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE memories SET access_count = access_count + 1, last_accessed = %s
                    WHERE id = %s
                """, (now, memory_id))

    def delete(self, memory_id: str) -> bool:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memory_edges WHERE source_id = %s OR target_id = %s",
                           (memory_id, memory_id))
                cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                return cur.rowcount > 0

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memory_edges (source_id, target_id, relation, weight, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (source_id, target_id, relation, weight, datetime.now(timezone.utc).isoformat()))

    def get_connected(self, memory_id: str, relation: str = None):
        conditions = ["(source_id = %s OR target_id = %s)"]
        params = [memory_id, memory_id]
        if relation:
            conditions.append("relation = %s")
            params.append(relation)

        where = " AND ".join(conditions)
        sql = f"""
            SELECT DISTINCT m.* FROM memories m
            JOIN memory_edges e ON (m.id = e.target_id OR m.id = e.source_id)
            WHERE {where}
        """

        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [self._row_to_record(r) for r in rows]

    def get_stats(self) -> dict:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as total FROM memories")
                total = cur.fetchone()["total"]
                cur.execute("SELECT memory_type, COUNT(*) as cnt FROM memories GROUP BY memory_type")
                by_type = {row["memory_type"]: row["cnt"] for row in cur.fetchall()}
                cur.execute("SELECT COUNT(*) as total FROM memory_edges")
                edges = cur.fetchone()["total"]
                return {
                    "total_memories": total,
                    "by_type": by_type,
                    "total_edges": edges,
                }

    def _row_to_record(self, row):
        from memory_engine.stores.sqlite_store import MemoryRecord
        return MemoryRecord(
            id=row["id"],
            memory_type=row["memory_type"],
            content=row["content"],
            context=row["context_json"] if isinstance(row["context_json"], dict) else json.loads(row["context_json"]),
            importance=row["importance"],
            confidence=row["confidence"],
            source=row["source"],
            agent_id=row["agent_id"],
            mission_id=row["mission_id"],
            task_id=row["task_id"],
            tags=row["tags_json"] if isinstance(row["tags_json"], list) else json.loads(row["tags_json"]),
            access_count=row["access_count"],
            last_accessed=str(row["last_accessed"]) if row["last_accessed"] else None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            expires_at=str(row["expires_at"]) if row["expires_at"] else None,
            metadata=row["metadata_json"] if isinstance(row["metadata_json"], dict) else json.loads(row["metadata_json"]),
        )
