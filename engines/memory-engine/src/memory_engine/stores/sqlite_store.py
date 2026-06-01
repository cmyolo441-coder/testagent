"""SQLite Memory Store — Local-first persistent memory"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path


@dataclass
class MemoryRecord:
    id: str = field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:12]}")
    memory_type: str = "episodic"  # episodic, semantic, procedural, working
    content: str = ""
    context: dict = field(default_factory=dict)
    importance: float = 0.5  # 0-1
    confidence: float = 0.5  # 0-1
    source: str = "user"  # user, tool, agent, system
    agent_id: Optional[str] = None
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    embedding: Optional[list[float]] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "context": self.context,
            "importance": self.importance,
            "confidence": self.confidence,
            "source": self.source,
            "agent_id": self.agent_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "tags": self.tags,
            "access_count": self.access_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


class SQLiteMemoryStore:
    """SQLite-backed persistent memory store."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_json TEXT DEFAULT '{}',
                    importance REAL DEFAULT 0.5,
                    confidence REAL DEFAULT 0.5,
                    source TEXT DEFAULT 'user',
                    agent_id TEXT,
                    mission_id TEXT,
                    task_id TEXT,
                    tags_json TEXT DEFAULT '[]',
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES memories(id),
                    FOREIGN KEY (target_id) REFERENCES memories(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_consolidations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ids TEXT NOT NULL,
                    result_id TEXT,
                    strategy TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (result_id) REFERENCES memories(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_mission ON memories(mission_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC)")
            conn.commit()

    def store(self, record: MemoryRecord) -> str:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories
                (id, memory_type, content, context_json, importance, confidence, source,
                 agent_id, mission_id, task_id, tags_json, access_count, last_accessed,
                 created_at, updated_at, expires_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.memory_type, record.content,
                json.dumps(record.context), record.importance, record.confidence,
                record.source, record.agent_id, record.mission_id, record.task_id,
                json.dumps(record.tags), record.access_count, record.last_accessed,
                record.created_at, record.updated_at, record.expires_at,
                json.dumps(record.metadata),
            ))
            conn.commit()
        return record.id

    def retrieve(self, memory_id: str) -> Optional[MemoryRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def search(self, query: str = None, memory_type: str = None,
               mission_id: str = None, tags: list[str] = None,
               min_importance: float = 0.0, limit: int = 20) -> list[MemoryRecord]:
        conditions = ["1=1"]
        params = []

        if query:
            conditions.append("content LIKE ?")
            params.append(f"%{query}%")
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)
        if mission_id:
            conditions.append("mission_id = ?")
            params.append(mission_id)
        if min_importance > 0:
            conditions.append("importance >= ?")
            params.append(min_importance)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM memories WHERE {where} ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def update_access(self, memory_id: str):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """, (now, memory_id))
            conn.commit()

    def delete(self, memory_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memory_edges WHERE source_id = ? OR target_id = ?", (memory_id, memory_id))
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return conn.total_changes > 0

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memory_edges (source_id, target_id, relation, weight, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source_id, target_id, relation, weight, datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_connected(self, memory_id: str, relation: str = None) -> list[MemoryRecord]:
        conditions = ["(source_id = ? OR target_id = ?)"]
        params = [memory_id, memory_id]
        if relation:
            conditions.append("relation = ?")
            params.append(relation)

        where = " AND ".join(conditions)
        sql = f"""
            SELECT m.* FROM memories m
            JOIN memory_edges e ON (m.id = e.target_id OR m.id = e.source_id)
            WHERE {where}
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").scalar()
            by_type = dict(conn.execute(
                "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type"
            ).fetchall())
            edges = conn.execute("SELECT COUNT(*) FROM memory_edges").scalar()
            return {
                "total_memories": total,
                "by_type": by_type,
                "total_edges": edges,
            }

    def _row_to_record(self, row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            memory_type=row["memory_type"],
            content=row["content"],
            context=json.loads(row["context_json"]),
            importance=row["importance"],
            confidence=row["confidence"],
            source=row["source"],
            agent_id=row["agent_id"],
            mission_id=row["mission_id"],
            task_id=row["task_id"],
            tags=json.loads(row["tags_json"]),
            access_count=row["access_count"],
            last_accessed=row["last_accessed"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row["expires_at"],
            metadata=json.loads(row["metadata_json"]),
        )
