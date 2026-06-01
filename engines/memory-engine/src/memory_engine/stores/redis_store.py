"""Redis Memory Store — Cache-based memory store with TTL"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisMemoryStore:
    """Redis-backed memory store for fast caching with TTL support."""

    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 0, password: str = None, prefix: str = "astra:mem:",
                 default_ttl: int = 86400):
        if not HAS_REDIS:
            raise ImportError("redis is required: pip install redis")

        self.client = redis.Redis(host=host, port=port, db=db, password=password)
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _key(self, memory_id: str) -> str:
        return f"{self.prefix}{memory_id}"

    def _search_key(self, tag: str) -> str:
        return f"{self.prefix}search:{tag}"

    def store(self, record, ttl: int = None) -> str:
        key = self._key(record.id)
        data = json.dumps(record.to_dict())
        effective_ttl = ttl or self.default_ttl

        pipe = self.client.pipeline()
        pipe.set(key, data, ex=effective_ttl)

        if record.memory_type:
            pipe.sadd(f"{self.prefix}types:{record.memory_type}", record.id)
        if record.mission_id:
            pipe.sadd(f"{self.prefix}missions:{record.mission_id}", record.id)
        if record.agent_id:
            pipe.sadd(f"{self.prefix}agents:{record.agent_id}", record.id)
        for tag in record.tags:
            pipe.sadd(self._search_key(tag), record.id)

        pipe.set(f"{self.prefix}importance:{record.id}", record.importance, ex=effective_ttl)
        pipe.execute()

        return record.id

    def retrieve(self, memory_id: str):
        data = self.client.get(self._key(memory_id))
        if not data:
            return None
        return self._dict_to_record(json.loads(data))

    def update_access(self, memory_id: str):
        self.client.incr(f"{self.prefix}access:{memory_id}")

    def delete(self, memory_id: str) -> bool:
        record = self.retrieve(memory_id)
        if not record:
            return False

        pipe = self.client.pipeline()
        pipe.delete(self._key(memory_id))
        pipe.delete(f"{self.prefix}access:{memory_id}")
        pipe.delete(f"{self.prefix}importance:{memory_id}")

        if record.memory_type:
            pipe.srem(f"{self.prefix}types:{record.memory_type}", memory_id)
        if record.mission_id:
            pipe.srem(f"{self.prefix}missions:{record.mission_id}", memory_id)
        if record.agent_id:
            pipe.srem(f"{self.prefix}agents:{record.agent_id}", memory_id)
        for tag in record.tags:
            pipe.srem(self._search_key(tag), memory_id)

        pipe.execute()
        return True

    def search(self, query: str = None, memory_type: str = None,
               mission_id: str = None, tags: list[str] = None,
               min_importance: float = 0.0, limit: int = 20):
        candidate_ids = set()

        if memory_type:
            type_ids = self.client.smembers(f"{self.prefix}types:{memory_type}")
            candidate_ids.update(mid.decode() for mid in type_ids)
        if mission_id:
            mission_ids = self.client.smembers(f"{self.prefix}missions:{mission_id}")
            candidate_ids.update(mid.decode() for mid in mission_ids)
        if tags:
            for tag in tags:
                tag_ids = self.client.smembers(self._search_key(tag))
                if not candidate_ids:
                    candidate_ids.update(mid.decode() for mid in tag_ids)
                else:
                    candidate_ids &= set(mid.decode() for mid in tag_ids)

        if not candidate_ids and not query and not min_importance:
            all_keys = self.client.keys(f"{self.prefix}[A-Z]*")
            candidate_ids.update(
                k.decode().replace(self.prefix, "")
                for k in all_keys
                if not any(x in k.decode() for x in (":types:", ":missions:", ":agents:", ":search:", ":access:", ":importance:"))
            )

        results = []
        for mid in candidate_ids:
            record = self.retrieve(mid)
            if not record:
                continue
            if query and query.lower() not in record.content.lower():
                continue
            if record.importance < min_importance:
                continue
            results.append(record)

        results.sort(key=lambda r: r.importance, reverse=True)
        return results[:limit]

    def get_by_type(self, memory_type: str, limit: int = 100):
        ids = self.client.smembers(f"{self.prefix}types:{memory_type}")
        results = []
        for mid in ids:
            record = self.retrieve(mid.decode())
            if record:
                results.append(record)
            if len(results) >= limit:
                break
        return results

    def get_by_mission(self, mission_id: str, limit: int = 100):
        ids = self.client.smembers(f"{self.prefix}missions:{mission_id}")
        results = []
        for mid in ids:
            record = self.retrieve(mid.decode())
            if record:
                results.append(record)
            if len(results) >= limit:
                break
        return results

    def set_ttl(self, memory_id: str, ttl: int):
        key = self._key(memory_id)
        self.client.expire(key, ttl)

    def get_ttl(self, memory_id: str) -> int:
        return self.client.ttl(self._key(memory_id))

    def get_access_count(self, memory_id: str) -> int:
        count = self.client.get(f"{self.prefix}access:{memory_id}")
        return int(count) if count else 0

    def bulk_store(self, records: list, ttl: int = None) -> list[str]:
        ids = []
        pipe = self.client.pipeline()
        effective_ttl = ttl or self.default_ttl

        for record in records:
            key = self._key(record.id)
            data = json.dumps(record.to_dict())
            pipe.set(key, data, ex=effective_ttl)

            if record.memory_type:
                pipe.sadd(f"{self.prefix}types:{record.memory_type}", record.id)
            if record.mission_id:
                pipe.sadd(f"{self.prefix}missions:{record.mission_id}", record.id)
            for tag in record.tags:
                pipe.sadd(self._search_key(tag), record.id)

            ids.append(record.id)

        pipe.execute()
        return ids

    def flush(self):
        keys = self.client.keys(f"{self.prefix}*")
        if keys:
            self.client.delete(*keys)

    def get_stats(self) -> dict:
        all_keys = self.client.keys(f"{self.prefix}[A-Z]*")
        memory_keys = [
            k for k in all_keys
            if not any(x in k.decode() for x in (":types:", ":missions:", ":agents:", ":search:", ":access:", ":importance:"))
        ]
        return {
            "total_memories": len(memory_keys),
            "prefix": self.prefix,
            "default_ttl": self.default_ttl,
        }

    def _dict_to_record(self, d: dict):
        from memory_engine.stores.sqlite_store import MemoryRecord
        return MemoryRecord(
            id=d.get("id", ""),
            memory_type=d.get("memory_type", "unknown"),
            content=d.get("content", ""),
            context=d.get("context", {}),
            importance=d.get("importance", 0.5),
            confidence=d.get("confidence", 0.5),
            source=d.get("source", "user"),
            agent_id=d.get("agent_id"),
            mission_id=d.get("mission_id"),
            task_id=d.get("task_id"),
            tags=d.get("tags", []),
            access_count=d.get("access_count", 0),
            last_accessed=d.get("last_accessed"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            expires_at=d.get("expires_at"),
            metadata=d.get("metadata", {}),
        )
