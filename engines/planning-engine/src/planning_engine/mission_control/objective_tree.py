"""Objective Tree — Hierarchical goal decomposition"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class ObjectiveType(Enum):
    GOAL = "goal"
    OBJECTIVE = "objective"
    KEY_RESULT = "key_result"
    TASK = "task"


class ObjectiveStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Objective:
    id: str = field(default_factory=lambda: f"OBJ-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    objective_type: ObjectiveType = ObjectiveType.TASK
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    parent_id: Optional[str] = None
    mission_id: Optional[str] = None
    children: list = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    risk_level: str = "low"
    priority: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.objective_type.value,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "mission_id": self.mission_id,
            "children": [c.id for c in self.children],
            "success_criteria": self.success_criteria,
            "risk_level": self.risk_level,
            "priority": self.priority,
        }


class ObjectiveTree:
    """Builds and manages hierarchical objective decomposition."""

    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.root: Optional[Objective] = None
        self.objectives: dict[str, Objective] = {}

    @classmethod
    def from_goal(cls, goal: str, mission_id: str) -> "ObjectiveTree":
        tree = cls(mission_id)
        root = Objective(
            title=goal,
            description=f"Primary goal: {goal}",
            objective_type=ObjectiveType.GOAL,
            mission_id=mission_id,
        )
        tree.root = root
        tree.objectives[root.id] = root

        # Auto-decompose into standard objectives
        sub_objectives = cls._decompose_goal(goal)
        for obj_data in sub_objectives:
            child = Objective(
                title=obj_data["title"],
                description=obj_data.get("description", ""),
                objective_type=ObjectiveType.OBJECTIVE,
                mission_id=mission_id,
                parent_id=root.id,
                success_criteria=obj_data.get("criteria", []),
                risk_level=obj_data.get("risk", "low"),
            )
            tree.objectives[child.id] = child
            root.children.append(child)

            # Add key results
            for kr in obj_data.get("key_results", []):
                kr_obj = Objective(
                    title=kr,
                    objective_type=ObjectiveType.KEY_RESULT,
                    mission_id=mission_id,
                    parent_id=child.id,
                )
                tree.objectives[kr_obj.id] = kr_obj
                child.children.append(kr_obj)

        return tree

    @staticmethod
    def _decompose_goal(goal: str) -> list[dict]:
        """Decompose a goal into standard objective categories."""
        goal_lower = goal.lower()
        objectives = []

        if any(w in goal_lower for w in ["company", "startup", "business", "software"]):
            objectives = [
                {
                    "title": "Market Research & Problem Validation",
                    "description": "Validate market need and problem significance",
                    "criteria": ["Market size validated", "Customer interviews completed"],
                    "risk": "low",
                    "key_results": ["Identify target audience", "Validate willingness to pay"],
                },
                {
                    "title": "Product Design & Architecture",
                    "description": "Design product and technical architecture",
                    "criteria": ["Architecture reviewed", "UX validated"],
                    "risk": "medium",
                    "key_results": ["Create product spec", "Design system architecture"],
                },
                {
                    "title": "MVP Development",
                    "description": "Build minimum viable product",
                    "criteria": ["Core features working", "Tests passing"],
                    "risk": "high",
                    "key_results": ["Backend API complete", "Frontend MVP ready"],
                },
                {
                    "title": "Security & Deployment",
                    "description": "Security audit and deployment setup",
                    "criteria": ["Security audit passed", "CI/CD working"],
                    "risk": "high",
                    "key_results": ["Security scan clean", "Production deployed"],
                },
                {
                    "title": "Launch & Growth",
                    "description": "Launch and iterate based on feedback",
                    "criteria": ["Users acquired", "Revenue generated"],
                    "risk": "medium",
                    "key_results": ["Marketing campaign live", "User feedback collected"],
                },
            ]
        else:
            objectives = [
                {
                    "title": "Research & Understanding",
                    "description": "Research the domain and understand requirements",
                    "criteria": ["Domain understood", "Requirements documented"],
                    "risk": "low",
                },
                {
                    "title": "Planning & Design",
                    "description": "Create detailed plan and design",
                    "criteria": ["Plan reviewed", "Design approved"],
                    "risk": "low",
                },
                {
                    "title": "Implementation",
                    "description": "Execute the main work",
                    "criteria": ["Core deliverables complete", "Quality verified"],
                    "risk": "medium",
                },
                {
                    "title": "Verification & Delivery",
                    "description": "Verify results and deliver",
                    "criteria": ["Verification passed", "Delivered successfully"],
                    "risk": "low",
                },
            ]
        return objectives

    def get_objective(self, obj_id: str) -> Optional[Objective]:
        return self.objectives.get(obj_id)

    def get_all_tasks(self) -> list[Objective]:
        return [
            obj for obj in self.objectives.values()
            if obj.objective_type in (ObjectiveType.TASK, ObjectiveType.KEY_RESULT)
        ]

    def calculate_progress(self) -> float:
        tasks = self.get_all_tasks()
        if not tasks:
            return 0.0
        done = sum(1 for t in tasks if t.status == ObjectiveStatus.COMPLETED)
        return done / len(tasks) * 100

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "root": self.root.to_dict() if self.root else None,
            "objectives": {k: v.to_dict() for k, v in self.objectives.items()},
            "progress": self.calculate_progress(),
        }
