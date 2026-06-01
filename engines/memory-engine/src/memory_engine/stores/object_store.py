"""Object Memory Store — Filesystem or S3 backed JSON memory store."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import boto3  # type: ignore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None  # type: ignore


class ObjectMemoryStore:
    """Object-store memory backend.

    Default backend = local filesystem; layout is::

        <root>/<memory_type>/<id>.json

    If `backend == "s3"`, requires `boto3`. Keys are
    `<prefix>/<memory_type>/<id>.json` under the given `bucket`.
    """

    def __init__(self, root_dir: str = "./astra_memory_store", backend: str = "fs",
                 bucket: str = None, prefix: str = "astra/memories",
                 s3_client=None, region_name: str = None):
        self.backend = backend
        self.root_dir = str(root_dir)
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")

        if backend == "s3":
            if not HAS_BOTO3:
                raise ImportError(
                    "boto3 is required for ObjectMemoryStore with backend='s3': pip install boto3"
                )
            if not bucket:
                raise ValueError("ObjectMemoryStore S3 backend requires `bucket`")
            self.s3 = s3_client or boto3.client("s3", region_name=region_name)
        elif backend == "fs":
            os.makedirs(self.root_dir, exist_ok=True)
        else:
            raise ValueError(f"Unsupported backend: {backend!r}")

    # ----- key/path helpers ------------------------------------------------

    def _fs_path(self, memory_type: str, memory_id: str) -> Path:
        type_dir = Path(self.root_dir) / memory_type
        type_dir.mkdir(parents=True, exist_ok=True)
        return type_dir / f"{memory_id}.json"

    def _s3_key(self, memory_type: str, memory_id: str) -> str:
        return f"{self.prefix}/{memory_type}/{memory_id}.json"

    def _record_payload(self, record) -> dict:
        d = record.to_dict() if hasattr(record, "to_dict") else dict(record.__dict__)
        d["embedding"] = list(record.embedding) if record.embedding is not None else None
        d["last_accessed"] = record.last_accessed
        d["expires_at"] = record.expires_at
        return d

    # ----- core ops --------------------------------------------------------

    def store(self, record) -> str:
        payload = self._record_payload(record)
        data = json.dumps(payload)
        if self.backend == "fs":
            path = self._fs_path(record.memory_type, record.id)
            with open(path, "w") as f:
                f.write(data)
        else:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=self._s3_key(record.memory_type, record.id),
                Body=data.encode("utf-8"),
                ContentType="application/json",
            )
        return record.id

    def retrieve(self, memory_id: str):
        # We need to scan memory_type folders because we don't know it upfront.
        if self.backend == "fs":
            for type_dir in Path(self.root_dir).iterdir() if Path(self.root_dir).exists() else []:
                if not type_dir.is_dir():
                    continue
                candidate = type_dir / f"{memory_id}.json"
                if candidate.exists():
                    with open(candidate) as f:
                        return self._dict_to_record(json.loads(f.read()))
            return None
        else:
            # List under prefix; filter for matching suffix.
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix + "/"):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if key.endswith(f"/{memory_id}.json"):
                        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
                        body = resp["Body"].read().decode("utf-8")
                        return self._dict_to_record(json.loads(body))
            return None

    def update_access(self, memory_id: str):
        rec = self.retrieve(memory_id)
        if rec is None:
            return
        rec.access_count = (rec.access_count or 0) + 1
        rec.last_accessed = datetime.now(timezone.utc).isoformat()
        self.store(rec)

    def delete(self, memory_id: str) -> bool:
        if self.backend == "fs":
            for type_dir in Path(self.root_dir).iterdir() if Path(self.root_dir).exists() else []:
                if not type_dir.is_dir():
                    continue
                candidate = type_dir / f"{memory_id}.json"
                if candidate.exists():
                    candidate.unlink()
                    return True
            return False
        else:
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix + "/"):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if key.endswith(f"/{memory_id}.json"):
                        self.s3.delete_object(Bucket=self.bucket, Key=key)
                        return True
            return False

    # ----- iteration -------------------------------------------------------

    def _iter_records(self, memory_type: str = None):
        if self.backend == "fs":
            root = Path(self.root_dir)
            if not root.exists():
                return
            dirs = [root / memory_type] if memory_type else [p for p in root.iterdir() if p.is_dir()]
            for type_dir in dirs:
                if not type_dir.exists():
                    continue
                for f in type_dir.glob("*.json"):
                    try:
                        with open(f) as fh:
                            yield self._dict_to_record(json.loads(fh.read()))
                    except Exception:
                        continue
        else:
            prefix = self.prefix + "/"
            if memory_type:
                prefix = f"{self.prefix}/{memory_type}/"
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if not key.endswith(".json"):
                        continue
                    try:
                        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
                        body = resp["Body"].read().decode("utf-8")
                        yield self._dict_to_record(json.loads(body))
                    except Exception:
                        continue

    def search(self, query=None, memory_type: str = None,
               mission_id: str = None, tags: list = None,
               min_importance: float = 0.0, limit: int = 20):
        results = []
        q = query.lower() if isinstance(query, str) and query else None
        tagset = set(tags) if tags else None

        for r in self._iter_records(memory_type=memory_type):
            if mission_id and r.mission_id != mission_id:
                continue
            if min_importance and (r.importance or 0.0) < min_importance:
                continue
            if tagset and not tagset.intersection(set(r.tags or [])):
                continue
            if q and q not in (r.content or "").lower():
                continue
            results.append(r)

        results.sort(key=lambda r: r.importance or 0.0, reverse=True)
        return results[:limit]

    def get_by_type(self, memory_type: str, limit: int = 100):
        out = []
        for r in self._iter_records(memory_type=memory_type):
            out.append(r)
            if len(out) >= limit:
                break
        return out

    def get_by_mission(self, mission_id: str, limit: int = 100):
        return self.search(mission_id=mission_id, limit=limit)

    def bulk_store(self, records) -> list:
        return [self.store(r) for r in records]

    def get_stats(self) -> dict:
        total = 0
        by_type: dict = {}
        if self.backend == "fs":
            root = Path(self.root_dir)
            if root.exists():
                for type_dir in root.iterdir():
                    if not type_dir.is_dir():
                        continue
                    count = sum(1 for _ in type_dir.glob("*.json"))
                    by_type[type_dir.name] = count
                    total += count
            return {
                "backend": "fs",
                "root_dir": self.root_dir,
                "total_memories": total,
                "by_type": by_type,
            }
        else:
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix + "/"):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if not key.endswith(".json"):
                        continue
                    # Layout: <prefix>/<memory_type>/<id>.json
                    rel = key[len(self.prefix) + 1:]
                    parts = rel.split("/", 1)
                    if len(parts) == 2:
                        mt = parts[0]
                        by_type[mt] = by_type.get(mt, 0) + 1
                        total += 1
            return {
                "backend": "s3",
                "bucket": self.bucket,
                "prefix": self.prefix,
                "total_memories": total,
                "by_type": by_type,
            }

    def _dict_to_record(self, d: dict):
        from memory_engine.stores.sqlite_store import MemoryRecord
        return MemoryRecord(
            id=d.get("id", ""),
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
