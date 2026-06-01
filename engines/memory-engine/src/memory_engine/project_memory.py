"""Project Memory — Track project states, milestones, and progress"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ProjectMilestone:
    name: str
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, blocked
    completed_at: Optional[str] = None


@dataclass
class ProjectState:
    id: str = field(default_factory=lambda: f"PRJ-{uuid.uuid4().hex[:12]}")
    project_id: str = ""
    project_name: str = ""
    status: str = "active"  # active, paused, completed, archived
    phase: str = "planning"  # planning, development, testing, deployment, maintenance
    progress: float = 0.0  # 0-100
    milestones: list[ProjectMilestone] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    team_members: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    last_checkpoint: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "status": self.status,
            "phase": self.phase,
            "progress": self.progress,
            "milestone_count": len(self.milestones),
            "blocker_count": len(self.blockers),
            "tags": self.tags,
            "updated_at": self.updated_at,
        }


class ProjectMemory:
    """Tracks project states, milestones, and historical progress."""

    def __init__(self, store=None):
        self.store = store
        self.states: dict[str, ProjectState] = {}
        self._project_index: dict[str, list[str]] = {}
        self._history: dict[str, list[dict]] = {}

    def store_project_state(self, project_id: str, project_name: str = "",
                            status: str = "active", phase: str = "planning",
                            progress: float = 0.0, milestones: list[dict] = None,
                            objectives: list[str] = None, blockers: list[str] = None,
                            team_members: list[str] = None, tags: list[str] = None,
                            metrics: dict = None) -> ProjectState:
        existing = self._find_by_project_id(project_id)
        if existing:
            self._snapshot(existing)
            existing.status = status
            existing.phase = phase
            existing.progress = progress
            existing.project_name = project_name or existing.project_name
            if milestones is not None:
                existing.milestones = [
                    ProjectMilestone(
                        name=m.get("name", ""),
                        description=m.get("description", ""),
                        status=m.get("status", "pending"),
                    )
                    for m in milestones
                ]
            if objectives is not None:
                existing.objectives = objectives
            if blockers is not None:
                existing.blockers = blockers
            if team_members is not None:
                existing.team_members = team_members
            if tags is not None:
                existing.tags = tags
            if metrics is not None:
                existing.metrics = metrics
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            return existing

        state = ProjectState(
            project_id=project_id,
            project_name=project_name,
            status=status,
            phase=phase,
            progress=progress,
            milestones=[
                ProjectMilestone(
                    name=m.get("name", ""),
                    description=m.get("description", ""),
                    status=m.get("status", "pending"),
                )
                for m in (milestones or [])
            ],
            objectives=objectives or [],
            blockers=blockers or [],
            team_members=team_members or [],
            tags=tags or [],
            metrics=metrics or {},
        )
        self.states[state.id] = state

        if project_id not in self._project_index:
            self._project_index[project_id] = []
        self._project_index[project_id].append(state.id)
        self._history[project_id] = []

        if self.store:
            from memory_engine.stores.sqlite_store import MemoryRecord
            record = MemoryRecord(
                memory_type="project",
                content=f"Project: {project_name} ({status}/{phase})",
                context={"project_id": project_id, "phase": phase, "progress": progress},
                importance=0.7,
                tags=tags or [],
                metadata={"project_state_id": state.id},
            )
            self.store.store(record)

        return state

    def get_state(self, project_id: str) -> Optional[ProjectState]:
        return self._find_by_project_id(project_id)

    def get_all_projects(self, status: str = None) -> list[ProjectState]:
        results = list(self.states.values())
        if status:
            results = [s for s in results if s.status == status]
        return results

    def get_history(self, project_id: str) -> list[dict]:
        return self._history.get(project_id, [])

    def _find_by_project_id(self, project_id: str) -> Optional[ProjectState]:
        state_ids = self._project_index.get(project_id, [])
        for sid in reversed(state_ids):
            if sid in self.states:
                return self.states[sid]
        return None

    def _snapshot(self, state: ProjectState):
        history = self._history.get(state.project_id, [])
        history.append({
            "status": state.status,
            "phase": state.phase,
            "progress": state.progress,
            "blockers": list(state.blockers),
            "timestamp": state.updated_at,
        })
        self._history[state.project_id] = history[-100:]

    def add_milestone(self, project_id: str, name: str, description: str = "") -> bool:
        state = self._find_by_project_id(project_id)
        if not state:
            return False
        state.milestones.append(ProjectMilestone(name=name, description=description))
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def complete_milestone(self, project_id: str, milestone_name: str) -> bool:
        state = self._find_by_project_id(project_id)
        if not state:
            return False
        for m in state.milestones:
            if m.name == milestone_name:
                m.status = "completed"
                m.completed_at = datetime.now(timezone.utc).isoformat()
                state.updated_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def add_blocker(self, project_id: str, blocker: str) -> bool:
        state = self._find_by_project_id(project_id)
        if not state:
            return False
        state.blockers.append(blocker)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def resolve_blocker(self, project_id: str, blocker: str) -> bool:
        state = self._find_by_project_id(project_id)
        if not state or blocker not in state.blockers:
            return False
        state.blockers.remove(blocker)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_stats(self) -> dict:
        states = list(self.states.values())
        by_status = {}
        for s in states:
            by_status[s.status] = by_status.get(s.status, 0) + 1
        return {
            "total_projects": len(states),
            "by_status": by_status,
            "total_blockers": sum(len(s.blockers) for s in states),
        }
