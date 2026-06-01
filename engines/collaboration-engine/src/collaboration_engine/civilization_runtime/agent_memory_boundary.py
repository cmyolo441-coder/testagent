"""Agent Memory Boundary — Enforces cross-agent memory access policies."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MemoryRecord:
    owner_id: str
    content: Any
    tags: list[str] = field(default_factory=list)
    scope: str = "private"  # private | team | public


@dataclass
class AccessPolicy:
    owner_id: str
    whitelist_viewers: set[str] = field(default_factory=set)
    blacklist_viewers: set[str] = field(default_factory=set)
    allowed_tags: set[str] = field(default_factory=set)
    blocked_tags: set[str] = field(default_factory=set)
    allowed_scopes: set[str] = field(default_factory=lambda: {"public"})


@dataclass
class AccessDecision:
    allowed: bool
    reason: str
    viewer_id: str = ""
    owner_id: str = ""


class AgentMemoryBoundary:
    """Govern what a viewer agent may read from an owner agent's memory."""

    def __init__(self):
        self.policies: dict[str, AccessPolicy] = {}

    def set_policy(self, policy: AccessPolicy) -> None:
        self.policies[policy.owner_id] = policy

    def get_or_create_policy(self, owner_id: str) -> AccessPolicy:
        if owner_id not in self.policies:
            self.policies[owner_id] = AccessPolicy(owner_id=owner_id)
        return self.policies[owner_id]

    def allow_viewer(self, owner_id: str, viewer_id: str) -> None:
        p = self.get_or_create_policy(owner_id)
        p.whitelist_viewers.add(viewer_id)
        p.blacklist_viewers.discard(viewer_id)

    def block_viewer(self, owner_id: str, viewer_id: str) -> None:
        p = self.get_or_create_policy(owner_id)
        p.blacklist_viewers.add(viewer_id)
        p.whitelist_viewers.discard(viewer_id)

    def allow_tag(self, owner_id: str, tag: str) -> None:
        self.get_or_create_policy(owner_id).allowed_tags.add(tag)

    def block_tag(self, owner_id: str, tag: str) -> None:
        self.get_or_create_policy(owner_id).blocked_tags.add(tag)

    def allow_scope(self, owner_id: str, scope: str) -> None:
        self.get_or_create_policy(owner_id).allowed_scopes.add(scope)

    def check_access(self, viewer_id: str, owner_id: str,
                     memory_record: MemoryRecord) -> AccessDecision:
        if viewer_id == owner_id:
            return AccessDecision(True, "owner accessing own memory", viewer_id, owner_id)
        policy = self.policies.get(owner_id)
        if policy is None:
            # default-deny except public scope
            if memory_record.scope == "public":
                return AccessDecision(True, "no policy; public scope", viewer_id, owner_id)
            return AccessDecision(False, "no policy; non-public denied", viewer_id, owner_id)

        if viewer_id in policy.blacklist_viewers:
            return AccessDecision(False, "viewer blacklisted", viewer_id, owner_id)

        record_tags = set(memory_record.tags)
        if policy.blocked_tags & record_tags:
            return AccessDecision(False, f"blocked tag(s): {sorted(policy.blocked_tags & record_tags)}",
                                  viewer_id, owner_id)

        if viewer_id in policy.whitelist_viewers:
            return AccessDecision(True, "viewer whitelisted", viewer_id, owner_id)

        if memory_record.scope not in policy.allowed_scopes:
            return AccessDecision(False, f"scope '{memory_record.scope}' not allowed",
                                  viewer_id, owner_id)

        if policy.allowed_tags and not (policy.allowed_tags & record_tags):
            return AccessDecision(False, "no overlapping allowed tag", viewer_id, owner_id)

        return AccessDecision(True, "scope+tag policy permits", viewer_id, owner_id)
