"""Resource Allocator — Allocate agents and resources to tasks"""
from dataclasses import dataclass, field


@dataclass
class Resource:
    id: str
    type: str  # agent, compute, budget
    capacity: float = 1.0
    allocated: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def available(self) -> float:
        return self.capacity - self.allocated


class ResourceAllocator:
    """Allocate resources to tasks based on priority and availability."""

    def __init__(self):
        self.resources: dict[str, Resource] = {}
        self.allocations: list[dict] = []

    def add_resource(self, resource: Resource):
        self.resources[resource.id] = resource

    def allocate(self, resource_id: str, task_id: str, amount: float) -> bool:
        resource = self.resources.get(resource_id)
        if not resource or resource.available < amount:
            return False
        resource.allocated += amount
        self.allocations.append({
            "resource_id": resource_id,
            "task_id": task_id,
            "amount": amount,
        })
        return True

    def release(self, resource_id: str, amount: float):
        resource = self.resources.get(resource_id)
        if resource:
            resource.allocated = max(0, resource.allocated - amount)

    def get_utilization(self) -> dict:
        return {
            rid: r.allocated / r.capacity if r.capacity > 0 else 0
            for rid, r in self.resources.items()
        }
