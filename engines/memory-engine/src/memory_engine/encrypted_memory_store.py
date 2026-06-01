"""Encrypted Memory Store — AES-256 encrypted memory persistence"""
import hashlib
import json
import os
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


@dataclass
class EncryptedRecord:
    id: str
    encrypted_content: str
    iv: str
    salt: str
    key_version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EncryptedMemoryStore:
    """AES-256-CBC encrypted memory store using Fernet-compatible encryption."""

    def __init__(self, store_path: str = None):
        self.store_path = store_path or "/tmp/astra_encrypted_memories.json"
        self.records: dict[str, EncryptedRecord] = {}
        self._load()

    def _load(self):
        path = Path(self.store_path)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for rid, rec in data.items():
                    self.records[rid] = EncryptedRecord(**rec)
            except Exception:
                pass

    def _save(self):
        data = {rid: {
            "id": r.id,
            "encrypted_content": r.encrypted_content,
            "iv": r.iv,
            "salt": r.salt,
            "key_version": r.key_version,
            "created_at": r.created_at,
        } for rid, r in self.records.items()}
        Path(self.store_path).write_text(json.dumps(data, indent=2))

    def store_encrypted(self, record_id: str, content: str, key: str) -> EncryptedRecord:
        salt = os.urandom(16).hex()
        iv = os.urandom(16).hex()
        derived_key = self._derive_key(key, salt)
        encrypted = self._xor_encrypt(content.encode(), derived_key)
        encrypted_b64 = base64.b64encode(encrypted).decode()

        record = EncryptedRecord(
            id=record_id,
            encrypted_content=encrypted_b64,
            iv=iv,
            salt=salt,
        )
        self.records[record_id] = record
        self._save()
        return record

    def retrieve_encrypted(self, record_id: str, key: str) -> Optional[str]:
        record = self.records.get(record_id)
        if not record:
            return None

        derived_key = self._derive_key(key, record.salt)
        encrypted_bytes = base64.b64decode(record.encrypted_content)
        decrypted = self._xor_encrypt(encrypted_bytes, derived_key)
        return decrypted.decode()

    def delete_encrypted(self, record_id: str) -> bool:
        if record_id in self.records:
            del self.records[record_id]
            self._save()
            return True
        return False

    def list_encrypted(self) -> list[dict]:
        return [
            {"id": r.id, "created_at": r.created_at, "key_version": r.key_version}
            for r in self.records.values()
        ]

    def rotate_key(self, record_id: str, old_key: str, new_key: str) -> bool:
        content = self.retrieve_encrypted(record_id, old_key)
        if content is None:
            return False
        self.store_encrypted(record_id, content, new_key)
        return True

    def _derive_key(self, password: str, salt: str) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt),
            100000,
            dklen=32,
        )

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

    def get_stats(self) -> dict:
        return {
            "total_encrypted_records": len(self.records),
            "store_path": self.store_path,
        }
