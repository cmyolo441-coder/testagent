"""Civilization Runtime — Agent society and institutions"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class InstitutionType(Enum):
    ACADEMY = "academy"
    GUILD = "guild"
    COUNCIL = "council"
    MINISTRY = "ministry"
    OFFICE = "office"
    STUDIO = "studio"
    LAB = "lab"
    DEPARTMENT = "department"
    DIVISION = "division"
    COURT = "court"


@dataclass
class Institution:
    id: str = field(default_factory=lambda: f"INST-{uuid.uuid4().hex[:8]}")
    name: str = ""
    institution_type: InstitutionType = InstitutionType.ACADEMY
    purpose: str = ""
    members: list[str] = field(default_factory=list)
    leadership: str = ""
    budget: float = 0
    performance_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.institution_type.value,
            "members_count": len(self.members),
            "performance": self.performance_metrics,
        }


class CivilizationRuntime:
    """Manage civilization runtime with institutions and governance."""

    def __init__(self):
        self.institutions: dict[str, Institution] = {}
        self.governance_log: list[dict] = []

    def create_institution(self, name: str, institution_type: InstitutionType, purpose: str) -> Institution:
        institution = Institution(name=name, institution_type=institution_type, purpose=purpose)
        self.institutions[institution.id] = institution
        return institution

    def get_institution(self, institution_id: str) -> Optional[Institution]:
        return self.institutions.get(institution_id)

    def list_institutions(self) -> list[dict]:
        return [inst.to_dict() for inst in self.institutions.values()]

    def record_governance_decision(self, decision: dict) -> None:
        self.governance_log.append({
            "timestamp": datetime.now().isoformat(),
            **decision,
        })