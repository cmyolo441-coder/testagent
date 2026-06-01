"""Procedural Memory — Store and recall action sequences and procedures"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ProcedureStep:
    step_id: int
    action: str
    parameters: dict = field(default_factory=dict)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    expected_duration_ms: int = 0


@dataclass
class Procedure:
    id: str = field(default_factory=lambda: f"PRC-{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    steps: list[ProcedureStep] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: float = 0.0
    tags: list[str] = field(default_factory=list)
    agent_id: Optional[str] = None
    mission_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_count": len(self.steps),
            "success_rate": self.success_rate,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class ProceduralMemory:
    """Manages procedural (how-to) memory for action sequences."""

    def __init__(self, store=None):
        self.store = store
        self.procedures: dict[str, Procedure] = {}
        self._name_index: dict[str, str] = {}

    def store_procedure(self, name: str, steps: list[dict],
                        description: str = "", tags: list[str] = None,
                        agent_id: str = None, mission_id: str = None) -> Procedure:
        existing_id = self._name_index.get(name.lower())
        if existing_id and existing_id in self.procedures:
            proc = self.procedures[existing_id]
            proc.steps = [
                ProcedureStep(
                    step_id=i,
                    action=s.get("action", ""),
                    parameters=s.get("parameters", {}),
                    preconditions=s.get("preconditions", []),
                    postconditions=s.get("postconditions", []),
                    expected_duration_ms=s.get("expected_duration_ms", 0),
                )
                for i, s in enumerate(steps)
            ]
            proc.description = description or proc.description
            proc.tags = tags or proc.tags
            proc.updated_at = datetime.now(timezone.utc).isoformat()
            return proc

        procedure = Procedure(
            name=name,
            description=description,
            steps=[
                ProcedureStep(
                    step_id=i,
                    action=s.get("action", ""),
                    parameters=s.get("parameters", {}),
                    preconditions=s.get("preconditions", []),
                    postconditions=s.get("postconditions", []),
                    expected_duration_ms=s.get("expected_duration_ms", 0),
                )
                for i, s in enumerate(steps)
            ],
            tags=tags or [],
            agent_id=agent_id,
            mission_id=mission_id,
        )
        self.procedures[procedure.id] = procedure
        self._name_index[name.lower()] = procedure.id

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="procedural",
                content=f"Procedure: {name} ({len(steps)} steps)",
                context={"name": name, "steps": [s.get("action", "") for s in steps]},
                importance=0.6,
                tags=tags or [],
                agent_id=agent_id,
                mission_id=mission_id,
                metadata={"procedure_id": procedure.id},
            )
            self.store.store(record)

        return procedure

    def recall(self, name: str) -> Optional[list[ProcedureStep]]:
        proc_id = self._name_index.get(name.lower())
        if proc_id and proc_id in self.procedures:
            return self.procedures[proc_id].steps
        return None

    def recall_by_id(self, procedure_id: str) -> Optional[Procedure]:
        return self.procedures.get(procedure_id)

    def search(self, query: str = None, tags: list[str] = None) -> list[Procedure]:
        results = list(self.procedures.values())
        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.description.lower()]
        if tags:
            tag_set = set(tags)
            results = [p for p in results if tag_set & set(p.tags)]
        return results

    def record_execution(self, procedure_id: str, success: bool, duration_ms: float):
        proc = self.procedures.get(procedure_id)
        if not proc:
            return
        if success:
            proc.success_count += 1
        else:
            proc.failure_count += 1
        total = proc.success_count + proc.failure_count
        proc.avg_duration_ms = (
            (proc.avg_duration_ms * (total - 1) + duration_ms) / total
        )
        proc.updated_at = datetime.now(timezone.utc).isoformat()

    def get_frequent(self, limit: int = 10) -> list[Procedure]:
        procs = sorted(
            self.procedures.values(),
            key=lambda p: p.success_count + p.failure_count,
            reverse=True,
        )
        return procs[:limit]

    def get_successful(self, min_rate: float = 0.8) -> list[Procedure]:
        return [
            p for p in self.procedures.values()
            if p.success_rate >= min_rate and (p.success_count + p.failure_count) > 0
        ]

    def get_stats(self) -> dict:
        procs = list(self.procedures.values())
        total_executions = sum(p.success_count + p.failure_count for p in procs)
        return {
            "total_procedures": len(procs),
            "total_executions": total_executions,
            "avg_success_rate": (
                sum(p.success_rate for p in procs) / len(procs) if procs else 0
            ),
        }
