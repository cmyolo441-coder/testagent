"""Chroma Memory Store — One Chroma Collection per memory_type."""
import json
from datetime import datetime, timezone
from typing import Optional

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    chromadb = None  # type: ignore


class ChromaMemoryStore:
    """ChromaDB-backed memory store.

    Maintains a separate Chroma Collection per memory_type so that
    metadata-only filters and query-text retrieval can be performed
    independently per memory class.
    """

    def __init__(self, persist_directory: str = None, collection_prefix: str = "astra_mem_",
                 client_kwargs: dict = None):
        if not HAS_CHROMA:
            raise ImportError(
                "chromadb is required for ChromaMemoryStore: pip install chromadb"
            )
        client_kwargs = client_kwargs or {}
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory, **client_kwargs)
        else:
            self.client = chromadb.Client(**client_kwargs)

        self.collection_prefix = collection_prefix
        self._collections: dict = {}
        # type registry collection to enumerate all known memory types.
        self._registry = self.client.get_or_create_collection(
            name=f"{collection_prefix}__registry__"
        )

    def _coll_name(self, memory_type: str) -> str:
        return f"{self.collection_prefix}{memory_type}"

    def _collection(self, memory_type: str):
        if memory_type not in self._collections:
            self._collections[memory_type] = self.client.get_or_create_collection(
                name=self._coll_name(memory_type)
            )
            # Record this type in the registry (idempotent upsert).
            try:
                self._registry.upsert(
                    ids=[memory_type],
                    documents=[memory_type],
                    metadatas=[{"memory_type": memory_type}],
                )
            except Exception:
                pass
        return self._collections[memory_type]

    def _record_metadata(self, record) -> dict:
        # Chroma metadata must be flat primitives; serialize nested structures.
        d = record.to_dict() if hasattr(record, "to_dict") else dict(record.__dict__)
        flat = {
            "id": d.get("id"),
            "memory_type": d.get("memory_type"),
            "importance": float(d.get("importance", 0.5)),
            "confidence": float(d.get("confidence", 0.5)),
            "source": d.get("source") or "",
            "agent_id": d.get("agent_id") or "",
            "mission_id": d.get("mission_id") or "",
            "task_id": d.get("task_id") or "",
            "access_count": int(d.get("access_count", 0)),
            "last_accessed": d.get("last_accessed") or "",
            "created_at": d.get("created_at") or "",
            "updated_at": d.get("updated_at") or "",
            "expires_at": d.get("expires_at") or "",
            "tags_json": json.dumps(d.get("tags", [])),
            "context_json": json.dumps(d.get("context", {})),
            "metadata_json": json.dumps(d.get("metadata", {})),
        }
        return flat

    def store(self, record) -> str:
        coll = self._collection(record.memory_type)
        kwargs = dict(
            ids=[record.id],
            documents=[record.content or ""],
            metadatas=[self._record_metadata(record)],
        )
        if record.embedding is not None:
            kwargs["embeddings"] = [list(record.embedding)]
        coll.upsert(**kwargs)
        return record.id

    def _list_memory_types(self) -> list:
        try:
            data = self._registry.get()
            return list(data.get("ids", []))
        except Exception:
            return list(self._collections.keys())

    def retrieve(self, memory_id: str):
        for mt in self._list_memory_types():
            coll = self._collection(mt)
            try:
                result = coll.get(ids=[memory_id], include=["metadatas", "documents", "embeddings"])
            except Exception:
                continue
            ids = result.get("ids") or []
            if ids:
                return self._chroma_to_record(result, 0)
        return None

    def update_access(self, memory_id: str):
        for mt in self._list_memory_types():
            coll = self._collection(mt)
            try:
                result = coll.get(ids=[memory_id], include=["metadatas"])
            except Exception:
                continue
            ids = result.get("ids") or []
            if not ids:
                continue
            md = (result.get("metadatas") or [{}])[0] or {}
            md["access_count"] = int(md.get("access_count", 0)) + 1
            md["last_accessed"] = datetime.now(timezone.utc).isoformat()
            coll.update(ids=[memory_id], metadatas=[md])
            return

    def delete(self, memory_id: str) -> bool:
        for mt in self._list_memory_types():
            coll = self._collection(mt)
            try:
                result = coll.get(ids=[memory_id])
            except Exception:
                continue
            if result.get("ids"):
                coll.delete(ids=[memory_id])
                return True
        return False

    def _metadata_where(self, mission_id=None, min_importance=0.0):
        where = {}
        clauses = []
        if mission_id:
            clauses.append({"mission_id": mission_id})
        if min_importance and min_importance > 0:
            clauses.append({"importance": {"$gte": float(min_importance)}})
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def search(self, query=None, memory_type: str = None,
               mission_id: str = None, tags: list = None,
               min_importance: float = 0.0, limit: int = 20):
        types = [memory_type] if memory_type else self._list_memory_types()
        results = []
        where = self._metadata_where(mission_id=mission_id, min_importance=min_importance)

        for mt in types:
            coll = self._collection(mt)
            if isinstance(query, str) and query:
                try:
                    res = coll.query(
                        query_texts=[query],
                        n_results=limit,
                        where=where,
                        include=["metadatas", "documents", "embeddings", "distances"],
                    )
                except Exception:
                    res = coll.query(query_texts=[query], n_results=limit,
                                     include=["metadatas", "documents"])
                ids = (res.get("ids") or [[]])[0]
                for i in range(len(ids)):
                    results.append(self._chroma_query_to_record(res, i))
            else:
                try:
                    res = coll.get(where=where, limit=limit,
                                   include=["metadatas", "documents", "embeddings"])
                except Exception:
                    res = coll.get(limit=limit, include=["metadatas", "documents"])
                ids = res.get("ids") or []
                for i in range(len(ids)):
                    results.append(self._chroma_to_record(res, i))

        if tags:
            tagset = set(tags)
            results = [r for r in results if tagset.intersection(set(r.tags or []))]

        results.sort(key=lambda r: r.importance or 0.0, reverse=True)
        return results[:limit]

    def get_by_type(self, memory_type: str, limit: int = 100):
        return self.search(memory_type=memory_type, limit=limit)

    def get_by_mission(self, mission_id: str, limit: int = 100):
        return self.search(mission_id=mission_id, limit=limit)

    def bulk_store(self, records) -> list:
        by_type: dict = {}
        for r in records:
            by_type.setdefault(r.memory_type, []).append(r)
        ids = []
        for mt, recs in by_type.items():
            coll = self._collection(mt)
            kwargs = dict(
                ids=[r.id for r in recs],
                documents=[r.content or "" for r in recs],
                metadatas=[self._record_metadata(r) for r in recs],
            )
            if all(r.embedding is not None for r in recs):
                kwargs["embeddings"] = [list(r.embedding) for r in recs]
            coll.upsert(**kwargs)
            ids.extend([r.id for r in recs])
        return ids

    def get_stats(self) -> dict:
        types = self._list_memory_types()
        by_type = {}
        total = 0
        for mt in types:
            coll = self._collection(mt)
            try:
                count = coll.count()
            except Exception:
                count = 0
            by_type[mt] = count
            total += count
        return {
            "backend": "chroma",
            "total_memories": total,
            "by_type": by_type,
            "collection_prefix": self.collection_prefix,
        }

    def _chroma_to_record(self, result: dict, index: int):
        md = (result.get("metadatas") or [{}])[index] or {}
        docs = result.get("documents") or []
        embs = result.get("embeddings") or []
        content = docs[index] if index < len(docs) else md.get("content", "")
        embedding = list(embs[index]) if index < len(embs) and embs[index] is not None else None
        return self._md_to_record(md, content=content, embedding=embedding)

    def _chroma_query_to_record(self, result: dict, index: int):
        md_list = (result.get("metadatas") or [[{}]])[0]
        md = md_list[index] if index < len(md_list) else {}
        docs = (result.get("documents") or [[]])[0]
        embs_outer = result.get("embeddings") or [[]]
        embs = embs_outer[0] if embs_outer else []
        content = docs[index] if index < len(docs) else (md or {}).get("content", "")
        embedding = list(embs[index]) if index < len(embs) and embs[index] is not None else None
        return self._md_to_record(md or {}, content=content, embedding=embedding)

    def _md_to_record(self, md: dict, content: str = "", embedding=None):
        from memory_engine.stores.sqlite_store import MemoryRecord
        return MemoryRecord(
            id=md.get("id", ""),
            memory_type=md.get("memory_type", "episodic"),
            content=content or "",
            context=json.loads(md.get("context_json", "{}") or "{}"),
            importance=float(md.get("importance", 0.5) or 0.5),
            confidence=float(md.get("confidence", 0.5) or 0.5),
            source=md.get("source") or "user",
            agent_id=md.get("agent_id") or None,
            mission_id=md.get("mission_id") or None,
            task_id=md.get("task_id") or None,
            tags=json.loads(md.get("tags_json", "[]") or "[]"),
            embedding=embedding,
            access_count=int(md.get("access_count", 0) or 0),
            last_accessed=md.get("last_accessed") or None,
            created_at=md.get("created_at") or datetime.now(timezone.utc).isoformat(),
            updated_at=md.get("updated_at") or datetime.now(timezone.utc).isoformat(),
            expires_at=md.get("expires_at") or None,
            metadata=json.loads(md.get("metadata_json", "{}") or "{}"),
        )
