"""Specialist Registry — Registry of role-bound specialists with skills."""
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Specialist:
    id: str = field(default_factory=lambda: f"SPEC-{uuid.uuid4().hex[:8]}")
    role: str = ""
    skills: list[str] = field(default_factory=list)
    cost_per_task: float = 1.0
    available: bool = True
    rating: float = 0.5


@dataclass
class TeamPlan:
    skills_required: list[str]
    members: list[Specialist]
    coverage: dict[str, list[str]]  # skill -> [specialist_ids]
    missing_skills: list[str]
    total_cost: float


class SpecialistRegistry:
    """Index specialists by role and skill."""

    def __init__(self):
        self.specialists: dict[str, Specialist] = {}

    def register_specialist(self, role: str, skills: list[str], cost_per_task: float = 1.0,
                            rating: float = 0.5) -> Specialist:
        spec = Specialist(role=role, skills=list(skills or []),
                          cost_per_task=cost_per_task, rating=rating)
        self.specialists[spec.id] = spec
        return spec

    def find_by_skill(self, skill: str) -> list[Specialist]:
        matches = [s for s in self.specialists.values()
                   if skill in s.skills and s.available]
        return sorted(matches, key=lambda s: (s.rating, -s.cost_per_task), reverse=True)

    def find_by_role(self, role: str) -> list[Specialist]:
        return [s for s in self.specialists.values() if s.role == role and s.available]

    def get_team_for_skills(self, skills_required: list[str]) -> TeamPlan:
        coverage: dict[str, list[str]] = {}
        chosen: dict[str, Specialist] = {}
        for skill in skills_required:
            ranked = self.find_by_skill(skill)
            coverage[skill] = [s.id for s in ranked]
            if ranked:
                # prefer someone already on the team
                already = next((s for s in ranked if s.id in chosen), None)
                pick = already or ranked[0]
                chosen[pick.id] = pick
        members = list(chosen.values())
        missing = [sk for sk, ids in coverage.items() if not ids]
        total_cost = sum(m.cost_per_task for m in members)
        return TeamPlan(
            skills_required=list(skills_required),
            members=members,
            coverage=coverage,
            missing_skills=missing,
            total_cost=total_cost,
        )

    def set_availability(self, specialist_id: str, available: bool) -> None:
        spec = self.specialists.get(specialist_id)
        if spec:
            spec.available = available

    def stats(self) -> dict:
        roles: dict[str, int] = {}
        for s in self.specialists.values():
            roles[s.role] = roles.get(s.role, 0) + 1
        return {
            "total": len(self.specialists),
            "available": sum(1 for s in self.specialists.values() if s.available),
            "roles": roles,
        }
