"""Role Factory — Create role definitions"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class RoleDefinition:
    id: str = field(default_factory=lambda: f"ROLE-{uuid.uuid4().hex[:8]}")
    name: str = ""
    specialization: str = ""
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    authority_level: int = 0  # 1-10
    reporting_to: str = ""
    max_holders: int = 1
    current_holders: int = 0
    compensation: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization,
            "authority_level": self.authority_level,
            "max_holders": self.max_holders,
            "current_holders": self.current_holders,
        }


class RoleFactory:
    """Create and manage role definitions for agents."""

    def __init__(self):
        self.roles: dict[str, RoleDefinition] = {}
        self.role_templates: dict[str, dict] = {
            "scientist": {
                "description": "Conducts research and experiments",
                "skills": ["research", "analysis", "experimentation"],
                "responsibilities": ["Conduct research", "Publish findings", "Mentor junior scientists"],
                "authority_level": 7,
            },
            "engineer": {
                "description": "Designs and builds systems",
                "skills": ["programming", "architecture", "problem_solving"],
                "responsibilities": ["Design systems", "Write code", "Review implementations"],
                "authority_level": 7,
            },
            "leader": {
                "description": "Leads teams and makes decisions",
                "skills": ["leadership", "decision_making", "communication"],
                "responsibilities": ["Set direction", "Allocate resources", "Resolve conflicts"],
                "authority_level": 9,
            },
            "analyst": {
                "description": "Analyzes data and provides insights",
                "skills": ["data_analysis", "statistics", "visualization"],
                "responsibilities": ["Analyze data", "Generate reports", "Provide recommendations"],
                "authority_level": 5,
            },
            "coordinator": {
                "description": "Coordinates activities across teams",
                "skills": ["coordination", "communication", "planning"],
                "responsibilities": ["Coordinate activities", "Track progress", "Report status"],
                "authority_level": 6,
            },
            "specialist": {
                "description": "Domain expert with deep knowledge",
                "skills": ["domain_expertise", "problem_solving", "mentoring"],
                "responsibilities": ["Provide expertise", "Guide decisions", "Train others"],
                "authority_level": 6,
            },
        }

    def create_role(self, specialization: str, customizations: dict = None) -> RoleDefinition:
        """Create a role definition for a specialization."""
        template = self.role_templates.get(specialization, self.role_templates["specialist"])
        
        role = RoleDefinition(
            name=f"{specialization.title()} Role",
            specialization=specialization,
            description=template.get("description", ""),
            required_skills=template.get("skills", []),
            responsibilities=template.get("responsibilities", []),
            authority_level=template.get("authority_level", 5),
        )
        
        if customizations:
            for key, value in customizations.items():
                if hasattr(role, key):
                    setattr(role, key, value)
        
        self.roles[role.id] = role
        return role

    def get_role(self, role_id: str) -> Optional[RoleDefinition]:
        return self.roles.get(role_id)

    def list_roles(self) -> list[dict]:
        return [role.to_dict() for role in self.roles.values()]

    def update_role(self, role_id: str, updates: dict) -> bool:
        role = self.roles.get(role_id)
        if not role:
            return False
        
        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)
        return True

    def find_roles_by_skill(self, skill: str) -> list[RoleDefinition]:
        """Find roles that require a specific skill."""
        return [role for role in self.roles.values() if skill in role.required_skills]

    def get_role_hierarchy(self) -> dict:
        """Get the role hierarchy based on authority levels."""
        sorted_roles = sorted(self.roles.values(), key=lambda r: r.authority_level, reverse=True)
        
        hierarchy = {}
        for role in sorted_roles:
            level = role.authority_level
            if level not in hierarchy:
                hierarchy[level] = []
            hierarchy[level].append(role.to_dict())
        
        return hierarchy