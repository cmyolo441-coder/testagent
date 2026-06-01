"""Snapshot Manager — Manage Firecracker microVM snapshots"""
import os
import json
import time
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Snapshot:
    snapshot_id: str
    vm_id: str
    snapshot_type: str  # "full" or "diff"
    mem_file_path: str
    disk_file_path: str
    created_at: float
    size_bytes: int
    version: int = 1
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "vm_id": self.vm_id,
            "snapshot_type": self.snapshot_type,
            "mem_file_path": self.mem_file_path,
            "disk_file_path": self.disk_file_path,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass
class RestoreResult:
    success: bool
    vm_id: str
    snapshot_id: str
    restore_time_ms: float
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "vm_id": self.vm_id,
            "snapshot_id": self.snapshot_id,
            "restore_time_ms": self.restore_time_ms,
            "error": self.error,
        }


class SnapshotManager:
    """Manage Firecracker microVM snapshots for fast restore."""

    SNAPSHOT_DIR = "/var/lib/sandbox-snapshots"

    def __init__(self, snapshot_dir: str = None):
        self.snapshot_dir = snapshot_dir or self.SNAPSHOT_DIR
        self._snapshots: dict[str, Snapshot] = {}
        self._ensure_dir()

    def _ensure_dir(self):
        Path(self.snapshot_dir).mkdir(parents=True, exist_ok=True)

    def snapshot(self, vm_id: str, mem_path: str = "",
                 disk_path: str = "", snapshot_type: str = "full",
                 metadata: dict = None) -> Snapshot:
        snapshot_id = f"snap-{vm_id}-{int(time.time())}"

        snap_mem = os.path.join(self.snapshot_dir, f"{snapshot_id}.mem")
        snap_disk = os.path.join(self.snapshot_dir, f"{snapshot_id}.disk")

        if mem_path and os.path.exists(mem_path):
            shutil.copy2(mem_path, snap_mem)
        else:
            Path(snap_mem).touch()

        if disk_path and os.path.exists(disk_path):
            shutil.copy2(disk_path, snap_disk)
        else:
            Path(snap_disk).touch()

        size = 0
        for f in [snap_mem, snap_disk]:
            if os.path.exists(f):
                size += os.path.getsize(f)

        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            vm_id=vm_id,
            snapshot_type=snapshot_type,
            mem_file_path=snap_mem,
            disk_file_path=snap_disk,
            created_at=time.time(),
            size_bytes=size,
            metadata=metadata or {},
        )

        self._snapshots[snapshot_id] = snapshot
        self._save_manifest()

        return snapshot

    def restore(self, snapshot_id: str, target_vm_id: str = "") -> RestoreResult:
        start = time.time()

        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            manifest = self._load_manifest()
            snapshot = manifest.get(snapshot_id)
            if not snapshot:
                return RestoreResult(
                    success=False,
                    vm_id=target_vm_id,
                    snapshot_id=snapshot_id,
                    restore_time_ms=0,
                    error=f"Snapshot not found: {snapshot_id}",
                )

        restored_vm_id = target_vm_id or f"restored-{snapshot.vm_id}-{int(time.time())}"

        mem_target = f"/tmp/{restored_vm_id}.mem"
        disk_target = f"/tmp/{restored_vm_id}.disk"

        try:
            if os.path.exists(snapshot.mem_file_path):
                shutil.copy2(snapshot.mem_file_path, mem_target)
            if os.path.exists(snapshot.disk_file_path):
                shutil.copy2(snapshot.disk_file_path, disk_target)

            restore_time = (time.time() - start) * 1000

            return RestoreResult(
                success=True,
                vm_id=restored_vm_id,
                snapshot_id=snapshot_id,
                restore_time_ms=restore_time,
            )
        except Exception as e:
            restore_time = (time.time() - start) * 1000
            return RestoreResult(
                success=False,
                vm_id=restored_vm_id,
                snapshot_id=snapshot_id,
                restore_time_ms=restore_time,
                error=str(e),
            )

    def list_snapshots(self, vm_id: str = None) -> list[Snapshot]:
        snaps = list(self._snapshots.values())
        if vm_id:
            snaps = [s for s in snaps if s.vm_id == vm_id]
        return sorted(snaps, key=lambda s: s.created_at, reverse=True)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        for path in [snapshot.mem_file_path, snapshot.disk_file_path]:
            if os.path.exists(path):
                os.remove(path)

        del self._snapshots[snapshot_id]
        self._save_manifest()
        return True

    def get_total_size(self) -> int:
        return sum(s.size_bytes for s in self._snapshots.values())

    def cleanup_old(self, max_count: int = 10):
        snaps = sorted(self._snapshots.values(), key=lambda s: s.created_at)
        while len(snaps) > max_count:
            old = snaps.pop(0)
            self.delete_snapshot(old.snapshot_id)

    def _save_manifest(self):
        manifest = {sid: s.to_dict() for sid, s in self._snapshots.items()}
        manifest_path = os.path.join(self.snapshot_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _load_manifest(self) -> dict:
        manifest_path = os.path.join(self.snapshot_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                return json.load(f)
        return {}
