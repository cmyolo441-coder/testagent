"""FAISS Memory Store — Local in-memory vector index with JSON sidecar."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import faiss  # type: ignore
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None  # type: ignore
    np = None  # type: ignore


class FAISSMemoryStore:
    """FAISS-backed vector memory store with in-memory record dict.

    - Uses IndexFlatL2 by default. If size exceeds `ivf_threshold`, rebuilds
      as an IVF index on next save/build.
    - Embeddings are required for `store`; non-vector searches fall back to
      linear filtering over the in-memory record dict.
    - Supports save(path) / load(path).
    """

    def __init__(self, dim: int = 384, ivf_threshold: int = 10000,
                 nlist: int = 100, path: str = None):
        if not HAS_FAISS:
            raise ImportError(
                "faiss and numpy are required for FAISSMemoryStore: pip install faiss-cpu numpy"
            )
        self.dim = dim
        self.ivf_threshold = ivf_threshold
        self.nlist = nlist
        self.index = faiss.IndexFlatL2(dim)
        # id_map: row position -> memory_id
        self.id_to_pos: dict = {}
        self.pos_to_id: dict = {}
        # full record dict keyed by id
        self.records: dict = {}
        if path and Path(path).exists():
            self.load(path)

    def _resize(self, new_dim: int):
        self.dim = new_dim
        self.index = faiss.IndexFlatL2(new_dim)
        # Re-add existing embeddings.
        embs = []
        ids = []
        for mid, rec in self.records.items():
            if rec.embedding is not None and len(rec.embedding) == new_dim:
                embs.append(rec.embedding)
                ids.append(mid)
        self.id_to_pos = {}
        self.pos_to_id = {}
        if embs:
            arr = np.array(embs, dtype="float32")
            self.index.add(arr)
            for i, mid in enumerate(ids):
                self.id_to_pos[mid] = i
                self.pos_to_id[i] = mid

    def _maybe_promote_to_ivf(self):
        if self.index.ntotal >= self.ivf_threshold and not isinstance(self.index, faiss.IndexIVFFlat):
            quantizer = faiss.IndexFlatL2(self.dim)
            ivf = faiss.IndexIVFFlat(quantizer, self.dim, self.nlist)
            # Gather all current vectors.
            vectors = []
            ids = []
            for mid, rec in self.records.items():
                if rec.embedding is not None and len(rec.embedding) == self.dim:
                    vectors.append(rec.embedding)
                    ids.append(mid)
            if vectors:
                arr = np.array(vectors, dtype="float32")
                ivf.train(arr)
                ivf.add(arr)
                self.index = ivf
                self.id_to_pos = {mid: i for i, mid in enumerate(ids)}
                self.pos_to_id = {i: mid for i, mid in enumerate(ids)}

    def store(self, record) -> str:
        if record.embedding is None:
            raise ValueError("FAISSMemoryStore.store requires record.embedding to be set")
        if len(record.embedding) != self.dim:
            self._resize(len(record.embedding))

        arr = np.array([record.embedding], dtype="float32")
        # If record already exists, remove its previous entry by rebuilding via overwrite map.
        if record.id in self.id_to_pos:
            # Mark older pos as orphaned by overwriting record only; vector stays but search
            # uses pos_to_id mapping. To keep correctness, rebuild from scratch.
            self.records[record.id] = record
            self._rebuild_index()
        else:
            pos = self.index.ntotal
            self.index.add(arr)
            self.id_to_pos[record.id] = pos
            self.pos_to_id[pos] = record.id
            self.records[record.id] = record
            self._maybe_promote_to_ivf()
        return record.id

    def _rebuild_index(self):
        ids = []
        vectors = []
        for mid, rec in self.records.items():
            if rec.embedding is not None and len(rec.embedding) == self.dim:
                ids.append(mid)
                vectors.append(rec.embedding)
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_to_pos = {}
        self.pos_to_id = {}
        if vectors:
            arr = np.array(vectors, dtype="float32")
            self.index.add(arr)
            for i, mid in enumerate(ids):
                self.id_to_pos[mid] = i
                self.pos_to_id[i] = mid
        self._maybe_promote_to_ivf()

    def retrieve(self, memory_id: str):
        return self.records.get(memory_id)

    def update_access(self, memory_id: str):
        rec = self.records.get(memory_id)
        if not rec:
            return
        rec.access_count = (rec.access_count or 0) + 1
        rec.last_accessed = datetime.now(timezone.utc).isoformat()

    def delete(self, memory_id: str) -> bool:
        if memory_id not in self.records:
            return False
        del self.records[memory_id]
        self._rebuild_index()
        return True

    def search(self, query=None, memory_type: str = None,
               mission_id: str = None, tags: list = None,
               min_importance: float = 0.0, limit: int = 20,
               query_vector: list = None):
        # If a vector is provided -> FAISS search, then filter.
        vec = query_vector
        if vec is None and isinstance(query, list):
            vec = query

        candidates = []
        if vec is not None and self.index.ntotal > 0:
            q = np.array([list(vec)], dtype="float32")
            if q.shape[1] != self.dim:
                # cannot search across dims; fall back to linear
                candidates = list(self.records.values())
            else:
                k = min(limit * 5, self.index.ntotal) or 1
                if isinstance(self.index, faiss.IndexIVFFlat):
                    self.index.nprobe = max(1, min(self.nlist, 10))
                distances, indices = self.index.search(q, k)
                for pos in indices[0]:
                    if pos == -1:
                        continue
                    mid = self.pos_to_id.get(int(pos))
                    if mid and mid in self.records:
                        candidates.append(self.records[mid])
        else:
            candidates = list(self.records.values())
            if isinstance(query, str) and query:
                ql = query.lower()
                candidates = [r for r in candidates if ql in (r.content or "").lower()]

        # Metadata filters
        filtered = []
        for r in candidates:
            if memory_type and r.memory_type != memory_type:
                continue
            if mission_id and r.mission_id != mission_id:
                continue
            if tags and not set(tags).intersection(set(r.tags or [])):
                continue
            if min_importance and (r.importance or 0.0) < min_importance:
                continue
            filtered.append(r)

        if vec is None:
            filtered.sort(key=lambda r: r.importance or 0.0, reverse=True)
        return filtered[:limit]

    def get_by_type(self, memory_type: str, limit: int = 100):
        return [r for r in self.records.values() if r.memory_type == memory_type][:limit]

    def get_by_mission(self, mission_id: str, limit: int = 100):
        return [r for r in self.records.values() if r.mission_id == mission_id][:limit]

    def bulk_store(self, records) -> list:
        ids = []
        for r in records:
            ids.append(self.store(r))
        return ids

    def get_stats(self) -> dict:
        index_type = type(self.index).__name__
        return {
            "backend": "faiss",
            "index_type": index_type,
            "total_memories": len(self.records),
            "indexed_vectors": int(self.index.ntotal),
            "dim": self.dim,
        }

    def save(self, path: str):
        path = str(path)
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        records_dump = {}
        for mid, rec in self.records.items():
            d = rec.to_dict() if hasattr(rec, "to_dict") else dict(rec.__dict__)
            d["embedding"] = list(rec.embedding) if rec.embedding is not None else None
            d["last_accessed"] = rec.last_accessed
            d["expires_at"] = rec.expires_at
            records_dump[mid] = d
        with open(os.path.join(path, "records.json"), "w") as f:
            f.write(json.dumps({
                "dim": self.dim,
                "ivf_threshold": self.ivf_threshold,
                "nlist": self.nlist,
                "id_to_pos": self.id_to_pos,
                "pos_to_id": {str(k): v for k, v in self.pos_to_id.items()},
                "records": records_dump,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }))

    def load(self, path: str):
        from memory_engine.stores.sqlite_store import MemoryRecord
        path = str(path)
        index_path = os.path.join(path, "index.faiss")
        records_path = os.path.join(path, "records.json")
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        with open(records_path) as f:
            data = json.loads(f.read())
        self.dim = data.get("dim", self.dim)
        self.ivf_threshold = data.get("ivf_threshold", self.ivf_threshold)
        self.nlist = data.get("nlist", self.nlist)
        self.id_to_pos = data.get("id_to_pos", {})
        self.pos_to_id = {int(k): v for k, v in data.get("pos_to_id", {}).items()}
        self.records = {}
        for mid, d in data.get("records", {}).items():
            self.records[mid] = MemoryRecord(
                id=d.get("id", mid),
                memory_type=d.get("memory_type", "episodic"),
                content=d.get("content", ""),
                context=d.get("context", {}) or {},
                importance=d.get("importance", 0.5),
                confidence=d.get("confidence", 0.5),
                source=d.get("source", "user"),
                agent_id=d.get("agent_id"),
                mission_id=d.get("mission_id"),
                task_id=d.get("task_id"),
                tags=d.get("tags", []) or [],
                embedding=d.get("embedding"),
                access_count=d.get("access_count", 0) or 0,
                last_accessed=d.get("last_accessed"),
                created_at=d.get("created_at") or datetime.now(timezone.utc).isoformat(),
                updated_at=d.get("updated_at") or datetime.now(timezone.utc).isoformat(),
                expires_at=d.get("expires_at"),
                metadata=d.get("metadata", {}) or {},
            )
