"""Signer — Cryptographic signing for audit events"""
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Signature:
    data_hash: str
    signature: str
    algorithm: str
    key_id: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "data_hash": self.data_hash,
            "signature": self.signature,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "timestamp": self.timestamp,
        }


class Signer:
    """Cryptographic signer for audit events using HMAC."""

    def __init__(self, key: bytes = None, key_id: str = "default"):
        self.key = key or secrets.token_bytes(32)
        self.key_id = key_id
        self.algorithm = "hmac-sha256"
        self._signature_count = 0

    def sign(self, data: dict | str) -> Signature:
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)

        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        signature_value = hmac.new(
            self.key, data_str.encode(), hashlib.sha256
        ).hexdigest()

        self._signature_count += 1

        return Signature(
            data_hash=data_hash,
            signature=signature_value,
            algorithm=self.algorithm,
            key_id=self.key_id,
            timestamp=time.time(),
        )

    def verify(self, data: dict | str, signature: Signature) -> bool:
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)

        expected_hash = hashlib.sha256(data_str.encode()).hexdigest()
        if signature.data_hash != expected_hash:
            return False

        expected_sig = hmac.new(
            self.key, data_str.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature.signature, expected_sig)

    def verify_signature(self, data: dict | str, signature_str: str,
                         key_id: str = None) -> bool:
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)

        expected_hash = hashlib.sha256(data_str.encode()).hexdigest()
        expected_sig = hmac.new(
            self.key, data_str.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature_str)

    def get_stats(self) -> dict:
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "signature_count": self._signature_count,
        }

    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        return secrets.token_bytes(length)

    def export_public_info(self) -> dict:
        key_fingerprint = hashlib.sha256(self.key).hexdigest()[:16]
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "fingerprint": key_fingerprint,
        }
