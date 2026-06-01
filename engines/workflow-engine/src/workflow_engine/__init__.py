"""Workflow Engine — DAG-based workflow execution"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
import uuid


class WorkflowStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    id: str = field(default_factory=lambda: f"STEP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    tool: str = ""
    arguments: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None


@dataclass
class Workflow:
    id: str = field(default_factory=lambda: f"WF-{uuid.uuid4().hex[:8]}")
    name: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: str = ""
    metadata: dict = field(default_factory=dict)


class WorkflowEngine:
    """Execute DAG-based workflows."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self.tool_executor = None

    def create_workflow(self, name: str, steps: list[dict]) -> Workflow:
        wf = Workflow(name=name)
        for step_data in steps:
            step = WorkflowStep(
                name=step_data.get("name", ""),
                tool=step_data.get("tool", ""),
                arguments=step_data.get("arguments", {}),
                dependencies=step_data.get("dependencies", []),
            )
            wf.steps.append(step)
        self.workflows[wf.id] = wf
        return wf

    def get_ready_steps(self, workflow_id: str) -> list[WorkflowStep]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return []
        completed = {s.id for s in wf.steps if s.status == "done"}
        return [
            s for s in wf.steps
            if s.status == "pending" and all(d in completed for d in s.dependencies)
        ]

    def execute_step(self, workflow_id: str, step_id: str) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        step = next((s for s in wf.steps if s.id == step_id), None)
        if not step or not self.tool_executor:
            return False
        result = self.tool_executor.execute(step.tool, step.arguments)
        step.result = result.output
        step.status = "done" if result.success else "failed"
        step.error = result.error
        return result.success

    def get_progress(self, workflow_id: str) -> dict:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return {"error": "Workflow not found"}
        total = len(wf.steps)
        done = sum(1 for s in wf.steps if s.status == "done")
        failed = sum(1 for s in wf.steps if s.status == "failed")
        return {"total": total, "done": done, "failed": failed, "progress": done / total * 100 if total else 0}
