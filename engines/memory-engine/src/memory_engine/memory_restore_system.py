"""Memory Restore System — Backup and restore memories"""
import json
import gzip
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import uuid


@dataclass
class BackupMetadata:
    id: str = field(default_factory=lambda: f"BUK-{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    memory_count: int = 0
    size_bytes: int = 0
    compressed: bool = True
    checksum: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BackupData:
    metadata: BackupMetadata
    memories: list[dict] = field(default_factory=list)
    version_data: list[dict] = field(default_factory=list)
    provenance_data: list[dict] = field(default_factory=list)


class MemoryRestoreSystem:
    """Manages memory backups and restoration."""

    def __init__(self, store=None, backup_dir: str = "/tmp/astra_memory_backups"):
        self.store = store
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backups: dict[str, BackupMetadata] = {}
        self._load_backup_index()

    def _load_backup_index(self):
        index_path = self.backup_dir / "index.json"
        if index_path.exists():
            try:
                data = json.loads(index_path.read_text())
                for bid, meta in data.items():
                    self.backups[bid] = BackupMetadata(**meta)
            except Exception:
                pass

    def _save_backup_index(self):
        data = {bid: {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "memory_count": m.memory_count,
            "size_bytes": m.size_bytes,
            "compressed": m.compressed,
            "checksum": m.checksum,
            "tags": m.tags,
            "created_at": m.created_at,
        } for bid, m in self.backups.items()}
        index_path = self.backup_dir / "index.json"
        index_path.write_text(json.dumps(data, indent=2))

    def backup(self, name: str = "", description: str = "",
               tags: list[str] = None, compress: bool = True) -> BackupMetadata:
        memories = []
        if self.store:
            all_memories = self.store.search(limit=100000)
            memories = [m.to_dict() for m in all_memories]

        metadata = BackupMetadata(
            name=name or f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            description=description,
            memory_count=len(memories),
            compressed=compress,
            tags=tags or [],
        )

        backup_data = {
            "metadata": {
                "id": metadata.id,
                "name": metadata.name,
                "description": metadata.description,
                "memory_count": metadata.memory_count,
                "compressed": compress,
                "tags": metadata.tags,
                "created_at": metadata.created_at,
            },
            "memories": memories,
        }

        raw_data = json.dumps(backup_data).encode()
        if compress:
            raw_data = gzip.compress(raw_data)

        metadata.size_bytes = len(raw_data)
        metadata.checksum = hashlib.sha256(raw_data).hexdigest()

        backup_path = self.backup_dir / f"{metadata.id}.json.gz" if compress else self.backup_dir / f"{metadata.id}.json"
        backup_path.write_bytes(raw_data)

        self.backups[metadata.id] = metadata
        self._save_backup_index()

        return metadata

    def restore(self, backup_id: str) -> Optional[list[dict]]:
        metadata = self.backups.get(backup_id)
        if not metadata:
            return None

        backup_path = self.backup_dir / f"{backup_id}.json.gz" if metadata.compressed else self.backup_dir / f"{backup_id}.json"
        if not backup_path.exists():
            return None

        raw_data = backup_path.read_bytes()
        import hashlib
        checksum = hashlib.sha256(raw_data).hexdigest()
        if checksum != metadata.checksum:
            raise ValueError(f"Backup checksum mismatch: expected {metadata.checksum}, got {checksum}")

        if metadata.compressed:
            raw_data = gzip.decompress(raw_data)

        backup_data = json.loads(raw_data)
        memories = backup_data.get("memories", [])

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            for mem_dict in memories:
                record = MemoryRecord(
                    id=mem_dict.get("id", ""),
                    memory_type=mem_dict.get("memory_type", "unknown"),
                    content=mem_dict.get("content", ""),
                    context=mem_dict.get("context", {}),
                    importance=mem_dict.get("importance", 0.5),
                    confidence=mem_dict.get("confidence", 0.5),
                    source=mem_dict.get("source", "user"),
                    agent_id=mem_dict.get("agent_id"),
                    mission_id=mem_dict.get("mission_id"),
                    task_id=mem_dict.get("task_id"),
                    tags=mem_dict.get("tags", []),
                    access_count=mem_dict.get("access_count", 0),
                    created_at=mem_dict.get("created_at", datetime.now(timezone.utc).isoformat()),
                    updated_at=mem_dict.get("updated_at", datetime.now(timezone.utc).isoformat()),
                    metadata=mem_dict.get("metadata", {}),
                )
                self.store.store(record)

        return memories

    def list_backups(self) -> list[BackupMetadata]:
        return sorted(self.backups.values(), key=lambda b: b.created_at, reverse=True)

    def delete_backup(self, backup_id: str) -> bool:
        metadata = self.backups.get(backup_id)
        if not metadata:
            return False

        suffix = ".json.gz" if metadata.compressed else ".json"
        backup_path = self.backup_dir / f"{backup_id}{suffix}"
        if backup_path.exists():
            backup_path.unlink()

        del self.backups[backup_id]
        self._save_backup_index()
        return True

    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        return self.backups.get(backup_id)

    def verify_backup(self, backup_id: str) -> dict:
        metadata = self.backups.get(backup_id)
        if not metadata:
            return {"verified": False, "error": "Backup not found"}

        suffix = ".json.gz" if metadata.compressed else ".json"
        backup_path = self.backup_dir / f"{backup_id}{suffix}"
        if not backup_path.exists():
            return {"verified": False, "error": "Backup file missing"}

        raw_data = backup_path.read_bytes()
        import hashlib
        actual_checksum = hashlib.sha256(raw_data).hexdigest()
        return {
            "verified": actual_checksum == metadata.checksum,
            "expected_checksum": metadata.checksum,
            "actual_checksum": actual_checksum,
            "size_bytes": len(raw_data),
        }

    def get_stats(self) -> dict:
        backups = list(self.backups.values())
        total_size = sum(b.size_bytes for b in backups)
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_memories_backed_up": sum(b.memory_count for b in backups),
        }
