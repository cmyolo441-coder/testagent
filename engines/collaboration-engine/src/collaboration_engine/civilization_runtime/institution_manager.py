"""Institution Manager — Manage institutions"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class InstitutionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESTRUCTURING = "restructuring"
    DISSOLVED = "dissolved"


@dataclass
class InstitutionRecord:
    id: str = field(default_factory=lambda: f"INST-{uuid.uuid4().hex[:8]}")
    name: str = ""
    institution_type: str = ""
    purpose: str = ""
    status: InstitutionStatus = InstitutionStatus.ACTIVE
    members: list[str] = field(default_factory=list)
    leadership: str = ""
    budget: float = 0
    performance: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.institution_type,
            "status": self.status.value,
            "members_count": len(self.members),
            "budget": self.budget,
        }


class InstitutionManager:
    """Manage institutions within the civilization."""

    def __init__(self):
        self.institutions: dict[str, InstitutionRecord] = {}
        self.inter_institution_relations: list[dict] = []

    def manage(self, institutions: list[dict]) -> dict:
        """Manage a list of institutions."""
        result = {"created": 0, "updated": 0, "errors": []}
        
        for inst_data in institutions:
            inst_id = inst_data.get("id")
            
            if inst_id and inst_id in self.institutions:
                # Update existing
                inst = self.institutions[inst_id]
                for key, value in inst_data.items():
                    if hasattr(inst, key) and key != "id":
                        setattr(inst, key, value)
                result["updated"] += 1
            else:
                # Create new
                record = InstitutionRecord(
                    name=inst_data.get("name", "Unknown"),
                    institution_type=inst_data.get("type", "general"),
                    purpose=inst_data.get("purpose", ""),
                    budget=inst_data.get("budget", 0),
                )
                self.institutions[record.id] = record
                result["created"] += 1
        
        result["total_institutions"] = len(self.institutions)
        return result

    def get_institution(self, institution_id: str) -> Optional[InstitutionRecord]:
        return self.institutions.get(institution_id)

    def add_member(self, institution_id: str, member_id: str) -> bool:
        inst = self.institutions.get(institution_id)
        if inst:
            if member_id not in inst.members:
                inst.members.append(member_id)
                return True
        return False

    def remove_member(self, institution_id: str, member_id: str) -> bool:
        inst = self.institutions.get(institution_id)
        if inst and member_id in inst.members:
            inst.members.remove(member_id)
            return True
        return False

    def update_performance(self, institution_id: str, metrics: dict) -> bool:
        inst = self.institutions.get(institution_id)
        if inst:
            inst.performance.update(metrics)
            return True
        return False

    def get_institution_stats(self) -> dict:
        if not self.institutions:
            return {"total": 0}
        
        total_members = sum(len(i.members) for i in self.institutions.values())
        total_budget = sum(i.budget for i in self.institutions.values())
        
        return {
            "total_institutions": len(self.institutions),
            "total_members": total_members,
            "total_budget": total_budget,
            "avg_members_per_institution": total_members / len(self.institutions),
        }

    def find_institutions_by_type(self, inst_type: str) -> list[InstitutionRecord]:
        return [i for i in self.institutions.values() if i.institution_type == inst_type]

    def record_inter_institution_relation(self, inst_a: str, inst_b: str, relation_type: str, details: dict = None):
        self.inter_institution_relations.append({
            "institution_a": inst_a,
            "institution_b": inst_b,
            "relation_type": relation_type,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        })

    def get_institution_network(self) -> dict:
        network = {"nodes": [], "edges": []}
        
        for inst in self.institutions.values():
            network["nodes"].append({
                "id": inst.id,
                "name": inst.name,
                "type": inst.institution_type,
                "size": len(inst.members),
            })
        
        for relation in self.inter_institution_relations:
            network["edges"].append({
                "source": relation["institution_a"],
                "target": relation["institution_b"],
                "type": relation["relation_type"],
            })
        
        return network