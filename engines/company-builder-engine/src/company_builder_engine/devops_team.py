"""DevOps Team — Plan infrastructure and deployment tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DevOpsTaskType(Enum):
    INFRASTRUCTURE = "infrastructure"
    CI_CD = "ci_cd"
    MONITORING = "monitoring"
    SECURITY = "security"
    AUTOMATION = "automation"
    DOCUMENTATION = "documentation"


@dataclass
class DevOpsTask:
    id: str = field(default_factory=lambda: f"DOTASK-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: DevOpsTaskType = DevOpsTaskType.INFRASTRUCTURE
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
            "tools": self.tools,
        }


@dataclass
class DevOpsPlan:
    id: str = field(default_factory=lambda: f"DOPLAN-{uuid.uuid4().hex[:8]}")
    cloud_provider: str = "AWS"
    tasks: list[DevOpsTask] = field(default_factory=list)
    infrastructure: dict = field(default_factory=dict)
    ci_cd_pipeline: dict = field(default_factory=dict)
    monitoring_stack: dict = field(default_factory=dict)
    security_measures: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cloud_provider": self.cloud_provider,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
        }


class DevOpsTeam:
    """Plan and coordinate infrastructure and deployment tasks."""

    def __init__(self):
        self.plans: dict[str, DevOpsPlan] = {}
        self.tasks: dict[str, DevOpsTask] = {}

    def plan(self, infrastructure: dict, requirements: list[str]) -> DevOpsPlan:
        """Plan DevOps tasks based on infrastructure requirements."""
        plan = DevOpsPlan(
            cloud_provider=infrastructure.get("cloud_provider", "AWS")
        )
        
        # Create tasks
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Design infrastructure
        plan.infrastructure = self._design_infrastructure(infrastructure)
        
        # Set up CI/CD pipeline
        plan.ci_cd_pipeline = self._setup_ci_cd_pipeline(requirements)
        
        # Configure monitoring
        plan.monitoring_stack = self._configure_monitoring(requirements)
        
        # Implement security measures
        plan.security_measures = self._implement_security(requirements)
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[DevOpsTask]:
        """Create DevOps tasks from requirements."""
        tasks = []
        
        # Infrastructure tasks
        infra_tasks = [
            ("Cloud Infrastructure Setup", DevOpsTaskType.INFRASTRUCTURE, 24, ["Terraform", "AWS CLI"]),
            ("Container Orchestration", DevOpsTaskType.INFRASTRUCTURE, 32, ["Docker", "Kubernetes"]),
            ("Database Setup", DevOpsTaskType.INFRASTRUCTURE, 16, ["PostgreSQL", "RDS"]),
            ("Cache Layer Setup", DevOpsTaskType.INFRASTRUCTURE, 8, ["Redis", "ElastiCache"]),
            ("Load Balancer Configuration", DevOpsTaskType.INFRASTRUCTURE, 12, ["ALB", "Nginx"]),
        ]
        
        for name, task_type, hours, tools in infra_tasks:
            task = DevOpsTask(
                name=name,
                description=f"Set up {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                tools=tools,
                acceptance_criteria=[
                    "Infrastructure as code implemented",
                    "Documentation updated",
                    "Security review completed",
                ],
            )
            tasks.append(task)
        
        # CI/CD tasks
        cicd_tasks = [
            ("CI Pipeline Setup", DevOpsTaskType.CI_CD, 16, ["GitHub Actions", "Jenkins"]),
            ("CD Pipeline Setup", DevOpsTaskType.CI_CD, 24, ["ArgoCD", "Spinnaker"]),
            ("Automated Testing", DevOpsTaskType.CI_CD, 20, ["Jest", "Cypress"]),
            ("Code Quality Checks", DevOpsTaskType.CI_CD, 12, ["SonarQube", "ESLint"]),
        ]
        
        for name, task_type, hours, tools in cicd_tasks:
            task = DevOpsTask(
                name=name,
                description=f"Set up {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                tools=tools,
            )
            tasks.append(task)
        
        # Monitoring tasks
        monitoring_tasks = [
            ("Metrics Collection", DevOpsTaskType.MONITORING, 16, ["Prometheus", "Grafana"]),
            ("Log Aggregation", DevOpsTaskType.MONITORING, 12, ["ELK Stack", "Loki"]),
            ("Distributed Tracing", DevOpsTaskType.MONITORING, 16, ["Jaeger", "Zipkin"]),
            ("Alerting Setup", DevOpsTaskType.MONITORING, 12, ["PagerDuty", "Slack"]),
        ]
        
        for name, task_type, hours, tools in monitoring_tasks:
            task = DevOpsTask(
                name=name,
                description=f"Set up {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                tools=tools,
            )
            tasks.append(task)
        
        # Security tasks
        security_tasks = [
            ("Security Scanning", DevOpsTaskType.SECURITY, 16, ["Snyk", "Trivy"]),
            ("Secret Management", DevOpsTaskType.SECURITY, 12, ["Vault", "AWS Secrets Manager"]),
            ("Network Security", DevOpsTaskType.SECURITY, 16, ["Security Groups", "WAF"]),
            ("Compliance Checks", DevOpsTaskType.SECURITY, 12, ["OpenSCAP", "Prowler"]),
        ]
        
        for name, task_type, hours, tools in security_tasks:
            task = DevOpsTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                tools=tools,
            )
            tasks.append(task)
        
        return tasks

    def _design_infrastructure(self, infrastructure: dict) -> dict:
        """Design infrastructure architecture."""
        return {
            "compute": {
                "kubernetes_cluster": {
                    "provider": infrastructure.get("cloud_provider", "AWS"),
                    "node_groups": [
                        {"name": "general", "instance_type": "m5.large", "min_nodes": 2, "max_nodes": 10},
                        {"name": "compute", "instance_type": "c5.large", "min_nodes": 1, "max_nodes": 5},
                    ],
                    "auto_scaling": True,
                },
            },
            "storage": {
                "object_storage": {"type": "S3", "versioning": True, "encryption": "AES-256"},
                "block_storage": {"type": "EBS", "type_param": "gp3", "encryption": True},
                "file_storage": {"type": "EFS", "encrypted": True},
            },
            "networking": {
                "vpc": {"cidr": "10.0.0.0/16", "enable_dns_hostnames": True},
                "subnets": {"public": ["10.0.1.0/24", "10.0.2.0/24"], "private": ["10.0.3.0/24", "10.0.4.0/24"]},
                "nat_gateway": True,
                "vpn": {"enabled": True, "type": "OpenVPN"},
            },
            "database": {
                "primary": {"engine": "PostgreSQL", "version": "14", "instance_type": "db.r5.large"},
                "read_replicas": 2,
                "backup": {"retention": 7, "automated": True},
            },
        }

    def _setup_ci_cd_pipeline(self, requirements: list[str]) -> dict:
        """Set up CI/CD pipeline."""
        return {
            "version_control": "GitHub",
            "ci_tool": "GitHub Actions",
            "cd_tool": "ArgoCD",
            "stages": [
                {
                    "name": "Lint",
                    "steps": ["ESLint", "Prettier", "TypeScript check"],
                    "parallel": True,
                },
                {
                    "name": "Test",
                    "steps": ["Unit tests", "Integration tests", "E2E tests"],
                    "parallel": False,
                },
                {
                    "name": "Build",
                    "steps": ["Docker build", "Push to ECR"],
                    "parallel": False,
                },
                {
                    "name": "Deploy",
                    "steps": ["Deploy to staging", "Smoke tests", "Deploy to production"],
                    "parallel": False,
                },
            ],
            "environments": ["development", "staging", "production"],
            "rollback_strategy": "Automated rollback on health check failure",
        }

    def _configure_monitoring(self, requirements: list[str]) -> dict:
        """Configure monitoring stack."""
        return {
            "metrics": {
                "collector": "Prometheus",
                "visualization": "Grafana",
                "dashboards": [
                    "Infrastructure Overview",
                    "Application Performance",
                    "Business Metrics",
                ],
                "alert_rules": [
                    {"metric": "cpu_usage", "threshold": 80, "duration": "5m"},
                    {"metric": "memory_usage", "threshold": 85, "duration": "5m"},
                    {"metric": "error_rate", "threshold": 5, "duration": "1m"},
                ],
            },
            "logging": {
                "collector": "Fluentd",
                "storage": "Elasticsearch",
                "visualization": "Kibana",
                "retention": "30 days",
            },
            "tracing": {
                "tool": "Jaeger",
                "sampling_rate": "1%",
                "propagation": "W3C Trace Context",
            },
            "alerting": {
                "channels": ["Slack", "Email", "PagerDuty"],
                "escalation_policies": [
                    {"level": 1, "delay": "5m", "channel": "Slack"},
                    {"level": 2, "delay": "15m", "channel": "Email"},
                    {"level": 3, "delay": "30m", "channel": "PagerDuty"},
                ],
            },
        }

    def _implement_security(self, requirements: list[str]) -> dict:
        """Implement security measures."""
        return {
            "authentication": {
                "method": "OAuth 2.0 + JWT",
                "mfa": True,
                "session_timeout": "24h",
            },
            "authorization": {
                "model": "RBAC",
                "roles": ["admin", "editor", "viewer"],
            },
            "data_protection": {
                "encryption_at_rest": "AES-256",
                "encryption_in_transit": "TLS 1.3",
                "key_management": "AWS KMS",
            },
            "network_security": {
                "firewall": "AWS Security Groups",
                "waf": "AWS WAF",
                "ddos_protection": "AWS Shield",
            },
            "compliance": {
                "frameworks": ["SOC 2", "GDPR"],
                "auditing": "Quarterly security audits",
                "penetration_testing": "Annual third-party testing",
            },
        }

    def _create_sprint_plan(self, tasks: list[DevOpsTask], team_size: int) -> list[dict]:
        """Create sprint plan for DevOps tasks."""
        sprints = []
        sprint_capacity = team_size * 40
        
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
        """Update task status."""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        task.status = status
        if hours > 0:
            task.actual_hours = hours
        
        return {"status": "updated", "task": task.to_dict()}

    def get_infrastructure_cost_estimate(self, plan_id: str) -> dict:
        """Get infrastructure cost estimate."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        return {
            "monthly_estimate": {
                "compute": 500,
                "storage": 100,
                "database": 300,
                "networking": 50,
                "monitoring": 100,
                "total": 1050,
            },
            "annual_estimate": 12600,
            "cost_optimization": [
                "Reserved instances for production",
                "Spot instances for development",
                "Auto-scaling to reduce idle resources",
            ],
        }

    def get_devops_insights(self) -> dict:
        """Get insights from DevOps plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "cloud_providers": list(set(p.cloud_provider for p in all_plans)),
        }