"""Product Manager — Create and manage product roadmaps"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime, timedelta


class RoadmapPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class RoadmapStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class RoadmapItem:
    id: str = field(default_factory=lambda: f"ITEM-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    priority: RoadmapPriority = RoadmapPriority.MEDIUM
    status: RoadmapStatus = RoadmapStatus.PLANNED
    estimated_effort: int = 0  # story points
    actual_effort: int = 0
    start_date: str = ""
    end_date: str = ""
    dependencies: list[str] = field(default_factory=list)
    assigned_team: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.value,
            "effort": self.estimated_effort,
            "team": self.assigned_team,
            "dependencies": len(self.dependencies),
        }


@dataclass
class ProductRoadmap:
    id: str = field(default_factory=lambda: f"ROADMAP-{uuid.uuid4().hex[:8]}")
    product_name: str = ""
    vision: str = ""
    items: list[RoadmapItem] = field(default_factory=list)
    milestones: list[dict] = field(default_factory=list)
    timeline_months: int = 6
    total_effort: int = 0
    completed_effort: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_name": self.product_name,
            "items_count": len(self.items),
            "total_effort": self.total_effort,
            "completed_effort": self.completed_effort,
            "progress": self.completed_effort / self.total_effort * 100 if self.total_effort > 0 else 0,
            "timeline_months": self.timeline_months,
        }


class ProductManager:
    """Create and manage product roadmaps."""

    def __init__(self):
        self.roadmaps: dict[str, ProductRoadmap] = {}
        self.items: dict[str, RoadmapItem] = {}
        self.sprint_duration_weeks = 2
        self.velocity_per_week = 20  # story points

    def create_roadmap(self, opportunities: list[dict], team_capacity: int = 100) -> ProductRoadmap:
        """Create a product roadmap from opportunities."""
        roadmap = ProductRoadmap()
        
        # Convert opportunities to roadmap items
        for i, opp in enumerate(opportunities[:10]):
            item = self._opportunity_to_item(opp, i)
            roadmap.items.append(item)
            self.items[item.id] = item
        
        # Calculate total effort
        roadmap.total_effort = sum(item.estimated_effort for item in roadmap.items)
        
        # Set timeline based on team capacity
        roadmap.timeline_months = max(3, roadmap.total_effort // (team_capacity // 3))
        
        # Create milestones
        roadmap.milestones = self._create_milestones(roadmap)
        
        # Assign teams
        self._assign_teams(roadmap)
        
        # Identify dependencies
        self._identify_dependencies(roadmap)
        
        self.roadmaps[roadmap.id] = roadmap
        return roadmap

    def _opportunity_to_item(self, opportunity: dict, index: int) -> RoadmapItem:
        """Convert an opportunity to a roadmap item."""
        # Estimate effort based on type
        effort_map = {
            "new_product": 40,
            "feature": 20,
            "improvement": 15,
            "integration": 25,
            "market_expansion": 30,
        }
        
        opp_type = opportunity.get("type", "feature")
        effort = effort_map.get(opp_type, 20)
        
        # Set priority based on score
        score = opportunity.get("overall_score", 0.5)
        if score > 0.8:
            priority = RoadmapPriority.CRITICAL
        elif score > 0.6:
            priority = RoadmapPriority.HIGH
        elif score > 0.4:
            priority = RoadmapPriority.MEDIUM
        else:
            priority = RoadmapPriority.LOW
        
        # Calculate dates
        start_date = datetime.now() + timedelta(weeks=index * 2)
        end_date = start_date + timedelta(weeks=effort // 10)
        
        return RoadmapItem(
            name=opportunity.get("name", f"Feature {index + 1}"),
            description=opportunity.get("description", ""),
            priority=priority,
            estimated_effort=effort,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            acceptance_criteria=[
                "Feature meets specifications",
                "Passes all tests",
                "User acceptance obtained",
            ],
        )

    def _create_milestones(self, roadmap: ProductRoadmap) -> list[dict]:
        """Create roadmap milestones."""
        milestones = []
        current_date = datetime.now()
        
        # Phase 1: Planning
        milestones.append({
            "name": "Planning Complete",
            "date": (current_date + timedelta(weeks=2)).isoformat(),
            "status": "pending",
            "items_required": [],
        })
        
        # Phase 2: MVP
        mvp_items = [item.id for item in roadmap.items if item.priority in [RoadmapPriority.CRITICAL, RoadmapPriority.HIGH]]
        milestones.append({
            "name": "MVP Ready",
            "date": (current_date + timedelta(weeks=8)).isoformat(),
            "status": "pending",
            "items_required": mvp_items[:3],
        })
        
        # Phase 3: Beta
        milestones.append({
            "name": "Beta Release",
            "date": (current_date + timedelta(weeks=16)).isoformat(),
            "status": "pending",
            "items_required": mvp_items,
        })
        
        # Phase 4: Launch
        milestones.append({
            "name": "Product Launch",
            "date": (current_date + timedelta(weeks=roadmap.timeline_months * 4)).isoformat(),
            "status": "pending",
            "items_required": [item.id for item in roadmap.items],
        })
        
        return milestones

    def _assign_teams(self, roadmap: ProductRoadmap):
        """Assign teams to roadmap items."""
        team_assignments = {
            "backend": ["API", "Database", "Server", "Integration"],
            "frontend": ["UI", "UX", "Design", "Interface"],
            "mobile": ["Mobile", "iOS", "Android", "App"],
            "devops": ["Deployment", "Infrastructure", "DevOps", "CI/CD"],
            "qa": ["Testing", "QA", "Quality", "Validation"],
        }
        
        for item in roadmap.items:
            assigned = False
            for team, keywords in team_assignments.items():
                for keyword in keywords:
                    if keyword.lower() in item.name.lower() or keyword.lower() in item.description.lower():
                        item.assigned_team = team
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                item.assigned_team = "backend"  # Default

    def _identify_dependencies(self, roadmap: ProductRoadmap):
        """Identify dependencies between items."""
        for i, item in enumerate(roadmap.items):
            # Simple dependency logic
            if i > 0 and item.assigned_team == roadmap.items[i-1].assigned_team:
                item.dependencies.append(roadmap.items[i-1].id)
            
            # Priority-based dependencies
            if item.priority == RoadmapPriority.LOW:
                high_priority_items = [it.id for it in roadmap.items if it.priority == RoadmapPriority.HIGH]
                if high_priority_items:
                    item.dependencies.append(high_priority_items[0])

    def update_item_status(self, item_id: str, status: RoadmapStatus, effort: int = 0) -> dict:
        """Update status of a roadmap item."""
        item = self.items.get(item_id)
        if not item:
            return {"error": "Item not found"}
        
        item.status = status
        if effort > 0:
            item.actual_effort = effort
        
        # Update roadmap progress
        self._update_roadmap_progress(item)
        
        return {"status": "updated", "item": item.to_dict()}

    def _update_roadmap_progress(self, item: RoadmapItem):
        """Update roadmap progress based on item status."""
        for roadmap in self.roadmaps.values():
            if any(ri.id == item.id for ri in roadmap.items):
                completed_items = [ri for ri in roadmap.items if ri.status == RoadmapStatus.COMPLETED]
                roadmap.completed_effort = sum(ri.actual_effort for ri in completed_items)
                roadmap.updated_at = datetime.now().isoformat()
                break

    def get_roadmap_status(self, roadmap_id: str) -> dict:
        """Get comprehensive roadmap status."""
        roadmap = self.roadmaps.get(roadmap_id)
        if not roadmap:
            return {"error": "Roadmap not found"}
        
        # Calculate metrics
        total_items = len(roadmap.items)
        completed_items = len([i for i in roadmap.items if i.status == RoadmapStatus.COMPLETED])
        in_progress_items = len([i for i in roadmap.items if i.status == RoadmapStatus.IN_PROGRESS])
        blocked_items = len([i for i in roadmap.items if i.status == RoadmapStatus.BLOCKED])
        
        # Team load
        team_load = {}
        for item in roadmap.items:
            team = item.assigned_team
            if team not in team_load:
                team_load[team] = {"total": 0, "completed": 0}
            team_load[team]["total"] += item.estimated_effort
            if item.status == RoadmapStatus.COMPLETED:
                team_load[team]["completed"] += item.actual_effort
        
        return {
            "roadmap": roadmap.to_dict(),
            "items_summary": {
                "total": total_items,
                "completed": completed_items,
                "in_progress": in_progress_items,
                "blocked": blocked_items,
            },
            "team_load": team_load,
            "milestones": roadmap.milestones,
            "risks": self._identify_roadmap_risks(roadmap),
        }

    def _identify_roadmap_risks(self, roadmap: ProductRoadmap) -> list[str]:
        """Identify risks in the roadmap."""
        risks = []
        
        # Check for bottlenecks
        blocked_items = [i for i in roadmap.items if i.status == RoadmapStatus.BLOCKED]
        if blocked_items:
            risks.append(f"{len(blocked_items)} items blocked")
        
        # Check for dependency chains
        max_dependency_chain = 0
        for item in roadmap.items:
            chain_length = len(item.dependencies)
            max_dependency_chain = max(max_dependency_chain, chain_length)
        
        if max_dependency_chain > 3:
            risks.append("Long dependency chains detected")
        
        # Check team overload
        team_load = {}
        for item in roadmap.items:
            team = item.assigned_team
            team_load[team] = team_load.get(team, 0) + item.estimated_effort
        
        for team, load in team_load.items():
            if load > 100:  # Threshold
                risks.append(f"Team {team} overloaded with {load} story points")
        
        return risks

    def reprioritize_items(self, roadmap_id: str, new_priorities: dict[str, int]) -> dict:
        """Reprioritize roadmap items."""
        roadmap = self.roadmaps.get(roadmap_id)
        if not roadmap:
            return {"error": "Roadmap not found"}
        
        for item in roadmap.items:
            if item.id in new_priorities:
                priority_value = new_priorities[item.id]
                item.priority = RoadmapPriority(priority_value)
        
        # Re-sort items by priority
        roadmap.items.sort(key=lambda i: i.priority.value)
        
        return {"status": "reprioritized", "items": len(roadmap.items)}

    def get_team_capacity_plan(self, roadmap_id: str) -> dict:
        """Get team capacity plan for the roadmap."""
        roadmap = self.roadmaps.get(roadmap_id)
        if not roadmap:
            return {"error": "Roadmap not found"}
        
        # Calculate capacity needs
        team_needs = {}
        for item in roadmap.items:
            team = item.assigned_team
            if team not in team_needs:
                team_needs[team] = {"effort": 0, "items": 0}
            team_needs[team]["effort"] += item.estimated_effort
            team_needs[team]["items"] += 1
        
        # Convert to capacity plan
        capacity_plan = {}
        for team, needs in team_needs.items():
            weeks_needed = needs["effort"] // self.velocity_per_week
            capacity_plan[team] = {
                "effort_needed": needs["effort"],
                "weeks_needed": weeks_needed,
                "team_size_needed": max(1, weeks_needed // roadmap.timeline_months),
                "items_count": needs["items"],
            }
        
        return capacity_plan