"""Failure Memory — Track failures, root causes, and patterns"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Failure:
    id: str = field(default_factory=lambda: f"FLR-{uuid.uuid4().hex[:12]}")
    title: str = ""
    description: str = ""
    failure_type: str = ""  # tool_error, task_failure, system_error, human_error, design_flaw
    severity: str = "medium"  # low, medium, high, critical
    root_cause: str = ""
    symptoms: list[str] = field(default_factory=list)
    resolution: str = ""
    resolution_status: str = "open"  # open, investigating, resolved, deferred
    impact: str = ""
    affected_components: list[str] = field(default_factory=list)
    related_failures: list[str] = field(default_factory=list)
    prevention_steps: list[str] = field(default_factory=list)
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "failure_type": self.failure_type,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "resolution_status": self.resolution_status,
            "impact": self.impact,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class FailureMemory:
    """Tracks failures, root causes, and patterns to prevent recurrence."""

    def __init__(self, store=None):
        self.store = store
        self.failures: dict[str, Failure] = {}
        self._type_index: dict[str, list[str]] = {}
        self._severity_index: dict[str, list[str]] = {}

    def store_failure(self, title: str, description: str = "",
                      failure_type: str = "unknown", severity: str = "medium",
                      root_cause: str = "", symptoms: list[str] = None,
                      impact: str = "", affected_components: list[str] = None,
                      mission_id: str = None, task_id: str = None,
                      agent_id: str = None, tags: list[str] = None) -> Failure:
        failure = Failure(
            title=title,
            description=description,
            failure_type=failure_type,
            severity=severity,
            root_cause=root_cause,
            symptoms=symptoms or [],
            impact=impact,
            affected_components=affected_components or [],
            mission_id=mission_id,
            task_id=task_id,
            agent_id=agent_id,
            tags=tags or [],
        )
        self.failures[failure.id] = failure

        if failure_type not in self._type_index:
            self._type_index[failure_type] = []
        self._type_index[failure_type].append(failure.id)

        if severity not in self._severity_index:
            self._severity_index[severity] = []
        self._severity_index[severity].append(failure.id)

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="failure",
                content=f"Failure: {title} ({failure_type}/{severity})",
                context={"failure_type": failure_type, "severity": severity},
                importance=0.9 if severity == "critical" else 0.6,
                tags=tags or [],
                mission_id=mission_id,
                task_id=task_id,
                agent_id=agent_id,
                metadata={"failure_id": failure.id},
            )
            self.store.store(record)

        return failure

    def get_patterns(self, min_occurrences: int = 2) -> list[dict]:
        patterns = []
        type_counts: dict[str, list[Failure]] = {}
        for f in self.failures.values():
            key = f.failure_type
            if key not in type_counts:
                type_counts[key] = []
            type_counts[key].append(f)

        for ftype, flist in type_counts.items():
            if len(flist) >= min_occurrences:
                common_tags = self._find_common_tags(flist)
                common_components = self._find_common_components(flist)
                patterns.append({
                    "failure_type": ftype,
                    "occurrence_count": len(flist),
                    "failure_ids": [f.id for f in flist],
                    "common_tags": common_tags,
                    "common_components": common_components,
                    "avg_severity": self._avg_severity_score(flist),
                    "most_common_root_cause": self._most_common_root_cause(flist),
                })

        patterns.sort(key=lambda p: p["occurrence_count"], reverse=True)
        return patterns

    def get_by_type(self, failure_type: str) -> list[Failure]:
        ids = self._type_index.get(failure_type, [])
        return [self.failures[fid] for fid in ids if fid in self.failures]

    def get_by_severity(self, severity: str) -> list[Failure]:
        ids = self._severity_index.get(severity, [])
        return [self.failures[fid] for fid in ids if fid in self.failures]

    def get_unresolved(self) -> list[Failure]:
        return [
            f for f in self.failures.values()
            if f.resolution_status in ("open", "investigating")
        ]

    def resolve(self, failure_id: str, resolution: str = "",
                prevention_steps: list[str] = None) -> bool:
        failure = self.failures.get(failure_id)
        if not failure:
            return False
        failure.resolution = resolution
        failure.resolution_status = "resolved"
        if prevention_steps:
            failure.prevention_steps = prevention_steps
        failure.resolved_at = datetime.now(timezone.utc).isoformat()
        failure.updated_at = failure.resolved_at
        return True

    def link_related(self, failure_id_a: str, failure_id_b: str) -> bool:
        a = self.failures.get(failure_id_a)
        b = self.failures.get(failure_id_b)
        if not a or not b:
            return False
        if failure_id_b not in a.related_failures:
            a.related_failures.append(failure_id_b)
        if failure_id_a not in b.related_failures:
            b.related_failures.append(failure_id_a)
        return True

    def get_prevention_recommendations(self, failure_type: str = None) -> list[str]:
        all_steps = []
        for f in self.failures.values():
            if failure_type and f.failure_type != failure_type:
                continue
            all_steps.extend(f.prevention_steps)
        seen = set()
        unique = []
        for step in all_steps:
            if step not in seen:
                seen.add(step)
                unique.append(step)
        return unique

    def _find_common_tags(self, failures: list[Failure]) -> list[str]:
        tag_counts: dict[str, int] = {}
        for f in failures:
            for t in f.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        return [t for t, c in tag_counts.items() if c >= 2]

    def _find_common_components(self, failures: list[Failure]) -> list[str]:
        comp_counts: dict[str, int] = {}
        for f in failures:
            for c in f.affected_components:
                comp_counts[c] = comp_counts.get(c, 0) + 1
        return [c for c, n in comp_counts.items() if n >= 2]

    def _avg_severity_score(self, failures: list[Failure]) -> float:
        score_map = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        scores = [score_map.get(f.severity, 0.5) for f in failures]
        return sum(scores) / len(scores) if scores else 0.5

    def _most_common_root_cause(self, failures: list[Failure]) -> str:
        causes = [f.root_cause for f in failures if f.root_cause]
        if not causes:
            return ""
        return max(set(causes), key=causes.count)

    def get_stats(self) -> dict:
        failures = list(self.failures.values())
        by_type = {}
        by_severity = {}
        by_status = {}
        for f in failures:
            by_type[f.failure_type] = by_type.get(f.failure_type, 0) + 1
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
            by_status[f.resolution_status] = by_status.get(f.resolution_status, 0) + 1
        return {
            "total_failures": len(failures),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
            "patterns_detected": len(self.get_patterns()),
        }
