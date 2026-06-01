"""Backend Team — Plan backend development tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class BackendTaskType(Enum):
    API_DEVELOPMENT = "api_development"
    DATABASE = "database"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION = "integration"
    OPTIMIZATION = "optimization"
    SECURITY = "security"


@dataclass
class BackendTask:
    id: str = field(default_factory=lambda: f"BTASK-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: BackendTaskType = BackendTaskType.API_DEVELOPMENT
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    dependencies: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    technical_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
            "assigned_to": self.assigned_to,
        }


@dataclass
class BackendPlan:
    id: str = field(default_factory=lambda: f"BPLAN-{uuid.uuid4().hex[:8]}")
    architecture: str = ""
    tasks: list[BackendTask] = field(default_factory=list)
    api_endpoints: list[dict] = field(default_factory=list)
    database_schema: dict = field(default_factory=dict)
    integrations: list[dict] = field(default_factory=list)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "architecture": self.architecture,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "team_size": self.team_size,
            "endpoints_count": len(self.api_endpoints),
        }


class BackendTeam:
    """Plan and coordinate backend development tasks."""

    def __init__(self):
        self.plans: dict[str, BackendPlan] = {}
        self.tasks: dict[str, BackendTask] = {}
        self.task_templates: dict[str, list[str]] = {
            "user_management": ["User registration", "Authentication", "Authorization", "Profile management"],
            "data_processing": ["Data validation", "Transformation", "Aggregation", "Export"],
            "api": ["REST endpoints", "GraphQL schema", "WebSocket handlers", "API documentation"],
            "database": ["Schema design", "Migrations", "Query optimization", "Backup strategy"],
            "security": ["Input validation", "Rate limiting", "Encryption", "Audit logging"],
        }

    def plan(self, architecture: dict, requirements: list[str]) -> BackendPlan:
        """Plan backend development based on architecture and requirements."""
        plan = BackendPlan(
            architecture=architecture.get("style", "monolith"),
            team_size=architecture.get("team_size", 5),
        )
        
        # Create tasks based on requirements
        plan.tasks = self._create_tasks(requirements, architecture)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Design API endpoints
        plan.api_endpoints = self._design_api_endpoints(requirements)
        
        # Create database schema
        plan.database_schema = self._create_database_schema(requirements)
        
        # Plan integrations
        plan.integrations = self._plan_integrations(requirements)
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str], architecture: dict) -> list[BackendTask]:
        """Create backend tasks from requirements."""
        tasks = []
        
        # Map requirements to tasks
        requirement_task_map = {
            "user": [
                ("User Registration API", BackendTaskType.API_DEVELOPMENT, 16),
                ("Authentication Service", BackendTaskType.SECURITY, 24),
                ("User Profile CRUD", BackendTaskType.API_DEVELOPMENT, 12),
                ("Role-Based Access Control", BackendTaskType.SECURITY, 20),
            ],
            "data": [
                ("Data Ingestion Pipeline", BackendTaskType.BUSINESS_LOGIC, 32),
                ("Data Validation Layer", BackendTaskType.BUSINESS_LOGIC, 16),
                ("Data Transformation Service", BackendTaskType.BUSINESS_LOGIC, 24),
                ("Data Export API", BackendTaskType.API_DEVELOPMENT, 12),
            ],
            "api": [
                ("REST API Framework", BackendTaskType.API_DEVELOPMENT, 20),
                ("API Documentation", BackendTaskType.API_DEVELOPMENT, 8),
                ("API Rate Limiting", BackendTaskType.SECURITY, 12),
                ("API Versioning", BackendTaskType.API_DEVELOPMENT, 8),
            ],
            "database": [
                ("Database Schema Design", BackendTaskType.DATABASE, 16),
                ("Database Migrations", BackendTaskType.DATABASE, 12),
                ("Query Optimization", BackendTaskType.OPTIMIZATION, 20),
                ("Backup Strategy", BackendTaskType.DATABASE, 8),
            ],
        }
        
        # Create tasks based on matching requirements
        for requirement in requirements:
            req_lower = requirement.lower()
            for key, task_list in requirement_task_map.items():
                if key in req_lower:
                    for name, task_type, hours in task_list:
                        task = BackendTask(
                            name=name,
                            description=f"Implement {name.lower()}",
                            task_type=task_type,
                            priority=len(tasks) + 1,
                            estimated_hours=hours,
                            acceptance_criteria=[
                                f"Feature implemented and tested",
                                "Documentation updated",
                                "Code review completed",
                            ],
                        )
                        tasks.append(task)
        
        # Add default tasks if none created
        if not tasks:
            default_tasks = [
                ("API Endpoint Development", BackendTaskType.API_DEVELOPMENT, 40),
                ("Database Setup", BackendTaskType.DATABASE, 24),
                ("Business Logic Implementation", BackendTaskType.BUSINESS_LOGIC, 60),
                ("Security Implementation", BackendTaskType.SECURITY, 32),
                ("Performance Optimization", BackendTaskType.OPTIMIZATION, 20),
            ]
            
            for name, task_type, hours in default_tasks:
                task = BackendTask(
                    name=name,
                    description=f"Implement {name.lower()}",
                    task_type=task_type,
                    priority=len(tasks) + 1,
                    estimated_hours=hours,
                )
                tasks.append(task)
        
        return tasks

    def _design_api_endpoints(self, requirements: list[str]) -> list[dict]:
        """Design API endpoints based on requirements."""
        endpoints = []
        
        # Default RESTful endpoints
        default_endpoints = [
            {"method": "GET", "path": "/api/v1/health", "description": "Health check"},
            {"method": "POST", "path": "/api/v1/auth/login", "description": "User login"},
            {"method": "POST", "path": "/api/v1/auth/register", "description": "User registration"},
            {"method": "GET", "path": "/api/v1/users/{id}", "description": "Get user profile"},
            {"method": "PUT", "path": "/api/v1/users/{id}", "description": "Update user profile"},
            {"method": "DELETE", "path": "/api/v1/users/{id}", "description": "Delete user"},
        ]
        
        # Add requirement-specific endpoints
        for requirement in requirements:
            req_lower = requirement.lower()
            if "product" in req_lower:
                endpoints.extend([
                    {"method": "GET", "path": "/api/v1/products", "description": "List products"},
                    {"method": "POST", "path": "/api/v1/products", "description": "Create product"},
                    {"method": "GET", "path": "/api/v1/products/{id}", "description": "Get product"},
                    {"method": "PUT", "path": "/api/v1/products/{id}", "description": "Update product"},
                    {"method": "DELETE", "path": "/api/v1/products/{id}", "description": "Delete product"},
                ])
            elif "order" in req_lower:
                endpoints.extend([
                    {"method": "GET", "path": "/api/v1/orders", "description": "List orders"},
                    {"method": "POST", "path": "/api/v1/orders", "description": "Create order"},
                    {"method": "GET", "path": "/api/v1/orders/{id}", "description": "Get order"},
                    {"method": "PUT", "path": "/api/v1/orders/{id}/status", "description": "Update order status"},
                ])
            elif "payment" in req_lower:
                endpoints.extend([
                    {"method": "POST", "path": "/api/v1/payments", "description": "Process payment"},
                    {"method": "GET", "path": "/api/v1/payments/{id}", "description": "Get payment status"},
                    {"method": "POST", "path": "/api/v1/payments/{id}/refund", "description": "Refund payment"},
                ])
        
        endpoints.extend(default_endpoints)
        
        return endpoints

    def _create_database_schema(self, requirements: list[str]) -> dict:
        """Create database schema based on requirements."""
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True},
                        {"name": "email", "type": "VARCHAR(255)", "unique": True},
                        {"name": "password_hash", "type": "VARCHAR(255)"},
                        {"name": "created_at", "type": "TIMESTAMP"},
                        {"name": "updated_at", "type": "TIMESTAMP"},
                    ],
                },
                {
                    "name": "sessions",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "UUID", "foreign_key": "users.id"},
                        {"name": "token", "type": "VARCHAR(255)"},
                        {"name": "expires_at", "type": "TIMESTAMP"},
                    ],
                },
            ],
            "indexes": [
                {"table": "users", "columns": ["email"]},
                {"table": "sessions", "columns": ["token"]},
                {"table": "sessions", "columns": ["user_id"]},
            ],
        }
        
        # Add tables based on requirements
        for requirement in requirements:
            req_lower = requirement.lower()
            if "product" in req_lower:
                schema["tables"].append({
                    "name": "products",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True},
                        {"name": "name", "type": "VARCHAR(255)"},
                        {"name": "description", "type": "TEXT"},
                        {"name": "price", "type": "DECIMAL(10,2)"},
                        {"name": "stock", "type": "INTEGER"},
                        {"name": "created_at", "type": "TIMESTAMP"},
                    ],
                })
            elif "order" in req_lower:
                schema["tables"].append({
                    "name": "orders",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "UUID", "foreign_key": "users.id"},
                        {"name": "total", "type": "DECIMAL(10,2)"},
                        {"name": "status", "type": "VARCHAR(50)"},
                        {"name": "created_at", "type": "TIMESTAMP"},
                    ],
                })
        
        return schema

    def _plan_integrations(self, requirements: list[str]) -> list[dict]:
        """Plan integrations with external services."""
        integrations = [
            {
                "name": "Email Service",
                "provider": "SendGrid/AWS SES",
                "purpose": "Transactional emails",
                "priority": "high",
                "estimated_hours": 8,
            },
            {
                "name": "Payment Gateway",
                "provider": "Stripe",
                "purpose": "Payment processing",
                "priority": "high",
                "estimated_hours": 16,
            },
            {
                "name": "File Storage",
                "provider": "AWS S3",
                "purpose": "File uploads and storage",
                "priority": "medium",
                "estimated_hours": 8,
            },
        ]
        
        # Add requirement-specific integrations
        for requirement in requirements:
            req_lower = requirement.lower()
            if "analytics" in req_lower:
                integrations.append({
                    "name": "Analytics Service",
                    "provider": "Google Analytics/Mixpanel",
                    "purpose": "User behavior tracking",
                    "priority": "medium",
                    "estimated_hours": 12,
                })
            elif "notification" in req_lower:
                integrations.append({
                    "name": "Push Notifications",
                    "provider": "Firebase/OneSignal",
                    "purpose": "Mobile and web notifications",
                    "priority": "medium",
                    "estimated_hours": 16,
                })
        
        return integrations

    def _create_sprint_plan(self, tasks: list[BackendTask], team_size: int) -> list[dict]:
        """Create sprint plan for backend tasks."""
        sprints = []
        sprint_capacity = team_size * 40  # 40 hours per developer per sprint
        
        current_sprint = []
        current_hours = 0
        sprint_number = 1
        
        for task in sorted(tasks, key=lambda t: t.priority):
            if current_hours + task.estimated_hours > sprint_capacity and current_sprint:
                sprints.append({
                    "sprint_number": sprint_number,
                    "tasks": [t.to_dict() for t in current_sprint],
                    "total_hours": current_hours,
                    "capacity_used": current_hours / sprint_capacity * 100,
                })
                current_sprint = []
                current_hours = 0
                sprint_number += 1
            
            current_sprint.append(task)
            current_hours += task.estimated_hours
        
        if current_sprint:
            sprints.append({
                "sprint_number": sprint_number,
                "tasks": [t.to_dict() for t in current_sprint],
                "total_hours": current_hours,
                "capacity_used": current_hours / sprint_capacity * 100,
            })
        
        return sprints

    def update_task_status(self, task_id: str, status: str, hours: float = 0) -> dict:
        """Update task status and actual hours."""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        task.status = status
        if hours > 0:
            task.actual_hours = hours
        
        return {"status": "updated", "task": task.to_dict()}

    def get_team_workload(self, plan_id: str) -> dict:
        """Get team workload analysis."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        workload = {}
        for task in plan.tasks:
            assignee = task.assigned_to or "unassigned"
            if assignee not in workload:
                workload[assignee] = {"tasks": 0, "hours": 0, "by_type": {}}
            
            workload[assignee]["tasks"] += 1
            workload[assignee]["hours"] += task.estimated_hours
            
            task_type = task.task_type.value
            if task_type not in workload[assignee]["by_type"]:
                workload[assignee]["by_type"][task_type] = 0
            workload[assignee]["by_type"][task_type] += 1
        
        return workload

    def get_backend_insights(self) -> dict:
        """Get insights from backend plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "average_task_hours": total_hours / total_tasks if total_tasks > 0 else 0,
            "task_types": self._count_task_types(all_plans),
        }

    def _count_task_types(self, plans: list[BackendPlan]) -> dict:
        """Count tasks by type."""
        type_counts = {}
        for plan in plans:
            for task in plan.tasks:
                task_type = task.task_type.value
                type_counts[task_type] = type_counts.get(task_type, 0) + 1
        return type_counts