"""Legal Checklist — Check legal requirements"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class LegalItem:
    id: str = field(default_factory=lambda: f"LEGAL-{uuid.uuid4().hex[:8]}")
    category: str = ""
    requirement: str = ""
    description: str = ""
    status: str = "pending"
    priority: str = "high"
    deadline: str = ""
    responsible: str = ""
    completed: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "category": self.category, "requirement": self.requirement, "status": self.status, "completed": self.completed}


@dataclass
class LegalChecklist:
    id: str = field(default_factory=lambda: f"LEGALCHECK-{uuid.uuid4().hex[:8]}")
    company_type: str = ""
    items: list[LegalItem] = field(default_factory=list)
    compliance_status: dict = field(default_factory=dict)
    total_items: int = 0
    completed_items: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"id": self.id, "company_type": self.company_type, "total_items": self.total_items, "completed_items": self.completed_items, "compliance_percentage": self.completed_items / self.total_items * 100 if self.total_items > 0 else 0}


class LegalChecklistEngine:
    """Check and manage legal requirements for companies."""

    def __init__(self):
        self.checklists: dict[str, LegalChecklist] = {}
        self.legal_requirements: dict[str, list[dict]] = {
            "startup": [
                {"category": "Entity Formation", "requirement": "Business Registration", "description": "Register business entity with state"},
                {"category": "Entity Formation", "requirement": "EIN Number", "description": "Obtain Employer Identification Number"},
                {"category": "Contracts", "requirement": "Founder Agreement", "description": "Document founder equity and responsibilities"},
                {"category": "Contracts", "requirement": "Terms of Service", "description": "Create terms of service for product"},
                {"category": "Privacy", "requirement": "Privacy Policy", "description": "Create privacy policy compliant with regulations"},
                {"category": "Intellectual Property", "requirement": "Trademark Registration", "description": "Register company name and logo"},
                {"category": "Employment", "requirement": "Employment Agreements", "description": "Create standard employment contracts"},
                {"category": "Compliance", "requirement": "Data Protection", "description": "GDPR/CCPA compliance if handling user data"},
                {"category": "Financial", "requirement": "Business Bank Account", "description": "Open dedicated business bank account"},
                {"category": "Insurance", "requirement": "General Liability Insurance", "description": "Obtain basic business insurance"},
            ],
            "corporation": [
                {"category": "Entity Formation", "requirement": "Articles of Incorporation", "description": "File with Secretary of State"},
                {"category": "Entity Formation", "requirement": "Corporate Bylaws", "description": "Establish corporate governance rules"},
                {"category": "Compliance", "requirement": "Board Resolutions", "description": "Document board decisions"},
                {"category": "Financial", "requirement": "Cap Table Management", "description": "Track equity ownership"},
                {"category": "Securities", "requirement": "SEC Compliance", "description": "Comply with securities regulations"},
            ],
            "llc": [
                {"category": "Entity Formation", "requirement": "Articles of Organization", "description": "File with Secretary of State"},
                {"category": "Entity Formation", "requirement": "Operating Agreement", "description": "Establish LLC operating rules"},
                {"category": "Compliance", "requirement": "Annual Reports", "description": "File annual state reports"},
                {"category": "Financial", "requirement": "EIN Number", "description": "Obtain tax identification number"},
            ],
        }

    def check(self, company_type: str) -> LegalChecklist:
        """Check legal requirements for a company type."""
        checklist = LegalChecklist(company_type=company_type)
        
        requirements = self.legal_requirements.get(company_type, self.legal_requirements["startup"])
        
        for req in requirements:
            item = LegalItem(
                category=req["category"],
                requirement=req["requirement"],
                description=req["description"],
                priority="high" if req["category"] in ["Entity Formation", "Compliance"] else "medium",
            )
            checklist.items.append(item)
        
        checklist.total_items = len(checklist.items)
        checklist.completed_items = 0
        checklist.compliance_status = self._calculate_compliance_status(checklist)
        
        self.checklists[checklist.id] = checklist
        return checklist

    def _calculate_compliance_status(self, checklist: LegalChecklist) -> dict:
        categories = {}
        for item in checklist.items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "completed": 0}
            categories[item.category]["total"] += 1
            if item.completed:
                categories[item.category]["completed"] += 1
        
        return categories

    def complete_item(self, checklist_id: str, item_id: str) -> dict:
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return {"error": "Checklist not found"}
        
        for item in checklist.items:
            if item.id == item_id:
                item.completed = True
                item.status = "completed"
                checklist.completed_items = sum(1 for i in checklist.items if i.completed)
                checklist.compliance_status = self._calculate_compliance_status(checklist)
                return {"status": "completed", "compliance_percentage": checklist.completed_items / checklist.total_items * 100}
        
        return {"error": "Item not found"}

    def get_legal_insights(self) -> dict:
        all_checklists = list(self.checklists.values())
        if not all_checklists:
            return {"status": "no_checklists"}
        
        total_items = sum(c.total_items for c in all_checklists)
        completed_items = sum(c.completed_items for c in all_checklists)
        
        return {
            "total_checklists": len(all_checklists),
            "total_items": total_items,
            "completed_items": completed_items,
            "overall_compliance": completed_items / total_items * 100 if total_items > 0 else 0,
        }