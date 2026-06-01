"""Merkle Chain — Merkle tree based audit chain for efficient verification"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MerkleNode:
    hash: str
    data: Optional[dict] = None
    left: Optional["MerkleNode"] = None
    right: Optional["MerkleNode"] = None
    is_leaf: bool = False
    index: int = 0


@dataclass
class ChainEntry:
    index: int
    data: dict
    leaf_hash: str
    path: list[str]
    root_hash: str


class MerkleChain:
    """Merkle tree based audit chain for efficient integrity verification."""

    def __init__(self):
        self.leaves: list[dict] = []
        self.tree: list[list[str]] = []
        self.root: Optional[str] = None
        self._entry_map: dict[str, dict] = {}

    @staticmethod
    def _hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        combined = left + right
        return hashlib.sha256(combined.encode()).hexdigest()

    def add(self, event: dict) -> ChainEntry:
        index = len(self.leaves)
        self.leaves.append(event)

        leaf_data = json.dumps(event, sort_keys=True, default=str)
        leaf_hash = self._hash(leaf_data)

        self._entry_map[leaf_hash] = event

        self._rebuild_tree()

        path = self._get_proof(index)
        root = self.root or ""

        return ChainEntry(
            index=index,
            data=event,
            leaf_hash=leaf_hash,
            path=path,
            root_hash=root,
        )

    def verify(self) -> bool:
        if not self.leaves:
            return True

        if not self.tree:
            return False

        expected_root = self._compute_root()
        return self.root == expected_root

    def verify_entry(self, index: int, event: dict) -> bool:
        if index < 0 or index >= len(self.leaves):
            return False

        leaf_data = json.dumps(event, sort_keys=True, default=str)
        expected_hash = self._hash(leaf_data)

        if self.leaves[index] != event:
            return False

        stored_hash = self._hash(json.dumps(self.leaves[index], sort_keys=True, default=str))
        return stored_hash == expected_hash

    def get_root(self) -> str:
        return self.root or ""

    def get_proof(self, index: int) -> list[str]:
        return self._get_proof(index)

    def get_entry(self, index: int) -> Optional[ChainEntry]:
        if index < 0 or index >= len(self.leaves):
            return None

        leaf_data = json.dumps(self.leaves[index], sort_keys=True, default=str)
        leaf_hash = self._hash(leaf_data)
        path = self._get_proof(index)

        return ChainEntry(
            index=index,
            data=self.leaves[index],
            leaf_hash=leaf_hash,
            path=path,
            root_hash=self.root or "",
        )

    def size(self) -> int:
        return len(self.leaves)

    def _rebuild_tree(self):
        if not self.leaves:
            self.tree = []
            self.root = None
            return

        current_level = []
        for i, leaf in enumerate(self.leaves):
            leaf_data = json.dumps(leaf, sort_keys=True, default=str)
            current_level.append(self._hash(leaf_data))

        self.tree = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left
                next_level.append(self._hash_pair(left, right))
            self.tree.append(next_level)
            current_level = next_level

        self.root = current_level[0] if current_level else None

    def _compute_root(self) -> Optional[str]:
        if not self.leaves:
            return None

        current_level = []
        for leaf in self.leaves:
            leaf_data = json.dumps(leaf, sort_keys=True, default=str)
            current_level.append(self._hash(leaf_data))

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_pair(left, right))
            current_level = next_level

        return current_level[0] if current_level else None

    def _get_proof(self, index: int) -> list[str]:
        if not self.tree or index < 0:
            return []

        proof = []
        current_index = index

        for level in self.tree[:-1]:
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1

            if sibling_index < len(level):
                proof.append(level[sibling_index])

            current_index //= 2

        return proof

    def export(self) -> list[dict]:
        return list(self.leaves)
