"""Qdrant Memory Store — Vector-search backed memory store."""
import json
from datetime import datetime, timezone
from typing import Optional

try:
    from qdrant_client import QdrantClient, models
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    QdrantClient = None  # type: ignore
    models = None  # type: ignore


class QdrantMemoryStore:
    """Qdrant-backed vector memory store."""

    def __init__(self, url: str = "http://localhost:6333", api_key: str = None,
                 collection_name: str = "astra_memories", vector_size: int = 384,
                 distance: str = "Cosine", recreate_on_dim_mismatch: bool = True,
                 path: str = None):
        if not HAS_QDRANT:
            raise ImportError(
                "qdrant-client is required for QdrantMemoryStore: pip install qdrant-client"
            )

        if path:
            self.client = QdrantClient(path=path)
        else:
            self.client = QdrantClient(url=url, api_key=api_key)

        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.recreate_on_dim_mismatch = recreate_on_dim_mismatch
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int):
        try:
            existing = self.client.get_collection(self.collection_name)
            existing_size = None
            try:
                existing_size = existing.config.params.vectors.size
            except Exception:
                existing_size = None
            if existing_size is not None and existing_size != vector_size and self.recreate_on_dim_mismatch:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=getattr(models.Distance, self.distance.upper(), models.Distance.COSINE),
                    ),
                )
                self.vector_size = vector_size
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=getattr(models.Distance, self.distance.upper(), models.Distance.COSINE),
                ),
            )
            self.vector_size = vector_size

    def _record_payload(self, record) -> dict:
        d = record.to_dict() if hasattr(record, "to_dict") else dict(record.__dict__)
        # Ensure JSON-serializable; exclude embedding from payload.
        d.pop("embedding", None)
        # Round-trip via json.dumps to enforce serializability.
        return json.loads(json.dumps(d, default=str))

    def store(self, record) -> str:
        if record.embedding is None:
            raise ValueError("QdrantMemoryStore.store requires record.embedding to be set")

        if len(record.embedding) != self.vector_size:
            self._ensure_collection(len(record.embedding))

        payload = self._record_payload(record)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=record.id,
                    vector=list(record.embedding),
                    payload=payload,
                )
            ],
        )
        return record.id

    def retrieve(self, memory_id: str):
        result = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[memory_id],
            with_payload=True,
            with_vectors=True,
        )
        if not result:
            return None
        point = result[0]
        return self._point_to_record(point)

    def update_access(self, memory_id: str):
        now = datetime.now(timezone.utc).isoformat()
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={"last_accessed": now},
            points=[memory_id],
        )
        # Increment access_count by reading then writing back.
        record = self.retrieve(memory_id)
        if record is not None:
            new_count = (record.access_count or 0) + 1
            self.client.set_payload(
                collection_name=self.collection_name,
                payload={"access_count": new_count},
                points=[memory_id],
            )

    def delete(self, memory_id: str) -> bool:
        existing = self.retrieve(memory_id)
        if existing is None:
            return False
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[memory_id]),
        )
        return True

    def _filter_from(self, memory_type=None, mission_id=None, tags=None, min_importance=0.0):
        must = []
        if memory_type:
            must.append(models.FieldCondition(key="memory_type",
                                              match=models.MatchValue(value=memory_type)))
        if mission_id:
            must.append(models.FieldCondition(key="mission_id",
                                              match=models.MatchValue(value=mission_id)))
        if tags:
            for tag in tags:
                must.append(models.FieldCondition(key="tags",
                                                  match=models.MatchValue(value=tag)))
        if min_importance and min_importance > 0:
            must.append(models.FieldCondition(
                key="importance",
                range=models.Range(gte=min_importance),
            ))
        if not must:
            return None
        return models.Filter(must=must)

    def search(self, query=None, memory_type: str = None,
               mission_id: str = None, tags: list = None,
               min_importance: float = 0.0, limit: int = 20,
               query_vector: list = None):
        flt = self._filter_from(memory_type, mission_id, tags, min_importance)

        # If a vector was supplied (preferred) use vector search.
        vec = query_vector
        if vec is None and isinstance(query, list):
            vec = query

        if vec is not None:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=list(vec),
                query_filter=flt,
                limit=limit,
                with_payload=True,
                with_vectors=True,
            )
            results = [self._point_to_record(h) for h in hits]
        else:
            # Scroll by filter; optional substring filter on `content`.
            scroll_filter = flt
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit * 4 if isinstance(query, str) else limit,
                with_payload=True,
                with_vectors=True,
            )
            records = [self._point_to_record(p) for p in points]
            if isinstance(query, str) and query:
                q = query.lower()
                records = [r for r in records if q in (r.content or "").lower()]
            records.sort(key=lambda r: r.importance, reverse=True)
            results = records[:limit]

        return results

    def get_by_type(self, memory_type: str, limit: int = 100):
        return self.search(memory_type=memory_type, limit=limit)

    def get_by_mission(self, mission_id: str, limit: int = 100):
        return self.search(mission_id=mission_id, limit=limit)

    def bulk_store(self, records) -> list:
        if not records:
            return []
        # Ensure dim consistency from first record with an embedding.
        first_with_emb = next((r for r in records if r.embedding is not None), None)
        if first_with_emb is None:
            raise ValueError("bulk_store requires at least one record with embedding")
        if len(first_with_emb.embedding) != self.vector_size:
            self._ensure_collection(len(first_with_emb.embedding))

        points = []
        ids = []
        for r in records:
            if r.embedding is None:
                continue
            points.append(models.PointStruct(
                id=r.id,
                vector=list(r.embedding),
                payload=self._record_payload(r),
            ))
            ids.append(r.id)
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
        return ids

    def get_stats(self) -> dict:
        try:
            info = self.client.get_collection(self.collection_name)
            count = getattr(info, "points_count", None)
            if count is None:
                count = self.client.count(self.collection_name, exact=True).count
        except Exception:
            count = 0
        return {
            "backend": "qdrant",
            "collection": self.collection_name,
            "vector_size": self.vector_size,
            "total_memories": count,
        }

    def _point_to_record(self, point):
        from memory_engine.stores.sqlite_store import MemoryRecord
        payload = getattr(point, "payload", None) or {}
        vector = getattr(point, "vector", None)
        return MemoryRecord(
            id=str(getattr(point, "id", payload.get("id", ""))),
            memory_type=payload.get("memory_type", "episodic"),
            content=payload.get("content", ""),
            context=payload.get("context", {}) or {},
            importance=payload.get("importance", 0.5),
            confidence=payload.get("confidence", 0.5),
            source=payload.get("source", "user"),
            agent_id=payload.get("agent_id"),
            mission_id=payload.get("mission_id"),
            task_id=payload.get("task_id"),
            tags=payload.get("tags", []) or [],
            embedding=list(vector) if vector is not None else None,
            access_count=payload.get("access_count", 0) or 0,
            last_accessed=payload.get("last_accessed"),
            created_at=payload.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=payload.get("updated_at", datetime.now(timezone.utc).isoformat()),
            expires_at=payload.get("expires_at"),
            metadata=payload.get("metadata", {}) or {},
        )
