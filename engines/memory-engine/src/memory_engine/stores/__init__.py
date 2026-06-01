"""Memory Stores — SQLite, Postgres, Redis backends"""

from memory_engine.stores.sqlite_store import SQLiteMemoryStore, MemoryRecord

__all__ = ["SQLiteMemoryStore", "MemoryRecord"]

try:
    from memory_engine.stores.postgres_store import PostgresMemoryStore
    __all__.append("PostgresMemoryStore")
except ImportError:
    pass

try:
    from memory_engine.stores.redis_store import RedisMemoryStore
    __all__.append("RedisMemoryStore")
except ImportError:
    pass
