"""Engineering Manager — Plan technical architecture"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class ArchitectureStyle(Enum):
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    HEXAGONAL = "hexagonal"


@dataclass
class TechnicalComponent:
    id: str = field(default_factory=lambda: f"COMP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    technology: str = ""
    responsibilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    estimated_effort: int = 0  # story points
    team: str = ""
    priority: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "technology": self.technology,
            "responsibilities": len(self.responsibilities),
            "dependencies": len(self.dependencies),
            "effort": self.estimated_effort,
            "team": self.team,
        }


@dataclass
class TechnicalPlan:
    id: str = field(default_factory=lambda: f"TECH-{uuid.uuid4().hex[:8]}")
    architecture_style: ArchitectureStyle = ArchitectureStyle.MONOLITH
    components: list[TechnicalComponent] = field(default_factory=list)
    infrastructure: dict = field(default_factory=dict)
    security_considerations: list[str] = field(default_factory=list)
    scalability_plan: dict = field(default_factory=dict)
    monitoring_strategy: dict = field(default_factory=dict)
    deployment_strategy: dict = field(default_factory=dict)
    technical_debt: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "architecture": self.architecture_style.value,
            "components_count": len(self.components),
            "total_effort": sum(c.estimated_effort for c in self.components),
            "teams_involved": list(set(c.team for c in self.components)),
        }


class EngineeringManager:
    """Plan technical architecture and coordinate engineering teams."""

    def __init__(self):
        self.plans: dict[str, TechnicalPlan] = {}
        self.components: dict[str, TechnicalComponent] = {}
        self.architecture_templates: dict[str, list[str]] = {
            "saas": ["user_auth", "api_gateway", "database", "cache", "background_jobs"],
            "ecommerce": ["product_catalog", "cart", "payment", "order_management", "inventory"],
            "social": ["user_profiles", "feed", "messaging", "notifications", "media"],
            "analytics": ["data_collection", "processing", "storage", "visualization", "export"],
        }

    def plan_architecture(self, roadmap: dict, team: list[dict]) -> TechnicalPlan:
        """Plan technical architecture based on product roadmap."""
        plan = TechnicalPlan()
        
        # Determine architecture style
        plan.architecture_style = self._determine_architecture_style(roadmap, team)
        
        # Create components
        plan.components = self._create_components(roadmap, team, plan.architecture_style)
        for comp in plan.components:
            self.components[comp.id] = comp
        
        # Plan infrastructure
        plan.infrastructure = self._plan_infrastructure(plan.components)
        
        # Define security considerations
        plan.security_considerations = self._define_security_considerations(plan.components)
        
        # Create scalability plan
        plan.scalability_plan = self._create_scalability_plan(plan.components)
        
        # Define monitoring strategy
        plan.monitoring_strategy = self._define_monitoring_strategy(plan.components)
        
        # Create deployment strategy
        plan.deployment_strategy = self._create_deployment_strategy(plan.architecture_style)
        
        # Identify technical debt
        plan.technical_debt = self._identify_technical_debt(plan.components)
        
        self.plans[plan.id] = plan
        return plan

    def _determine_architecture_style(self, roadmap: dict, team: list[dict]) -> ArchitectureStyle:
        """Determine appropriate architecture style."""
        team_size = len(team)
        complexity = roadmap.get("complexity", "medium")
        
        if team_size > 20 or complexity == "high":
            return ArchitectureStyle.MICROSERVICES
        elif team_size < 5 or complexity == "low":
            return ArchitectureStyle.MONOLITH
        else:
            return ArchitectureStyle.EVENT_DRIVEN

    def _create_components(self, roadmap: dict, team: list[dict], style: ArchitectureStyle) -> list[TechnicalComponent]:
        """Create technical components based on roadmap."""
        components = []
        
        # Core components based on architecture style
        core_components = {
            ArchitectureStyle.MONOLITH: [
                ("Application Core", "Central application logic", "Python/Django", ["backend"], 40),
                ("Database", "Data persistence layer", "PostgreSQL", ["backend"], 30),
                ("Web Interface", "User interface", "React", ["frontend"], 35),
                ("API Layer", "REST API endpoints", "Django REST", ["backend"], 25),
                ("Authentication", "User authentication", "JWT/OAuth", ["backend"], 20),
            ],
            ArchitectureStyle.MICROSERVICES: [
                ("User Service", "User management", "Node.js", ["backend"], 25),
                ("Product Service", "Product catalog", "Python/FastAPI", ["backend"], 30),
                ("Order Service", "Order processing", "Java/Spring", ["backend"], 35),
                ("Payment Service", "Payment processing", "Go", ["backend"], 30),
                ("API Gateway", "Request routing", "Kong/Nginx", ["devops"], 20),
                ("Message Queue", "Async communication", "RabbitMQ", ["devops"], 15),
                ("Web App", "Frontend application", "React", ["frontend"], 30),
                ("Mobile App", "Mobile application", "React Native", ["mobile"], 35),
            ],
            ArchitectureStyle.EVENT_DRIVEN: [
                ("Event Producer", "Generate events", "Python", ["backend"], 20),
                ("Event Bus", "Event routing", "Kafka", ["devops"], 25),
                ("Event Consumers", "Process events", "Various", ["backend"], 30),
                ("State Store", "State management", "Redis", ["backend"], 15),
                ("Web Interface", "Real-time UI", "React", ["frontend"], 30),
            ],
        }
        
        template_components = core_components.get(style, core_components[ArchitectureStyle.MONOLITH])
        
        for name, desc, tech, teams, effort in template_components:
            component = TechnicalComponent(
                name=name,
                description=desc,
                technology=tech,
                responsibilities=[f"Handle {name.lower()} operations"],
                estimated_effort=effort,
                team=teams[0] if teams else "backend",
                priority=len(components) + 1,
            )
            components.append(component)
        
        return components

    def _plan_infrastructure(self, components: list[TechnicalComponent]) -> dict:
        """Plan infrastructure requirements."""
        return {
            "cloud_provider": "AWS",
            "compute": {
                "type": "EKS" if len(components) > 5 else "EC2",
                "instances": max(2, len(components)),
                "auto_scaling": True,
            },
            "database": {
                "type": "RDS PostgreSQL",
                "multi_az": True,
                "backup": "Daily automated",
                "storage": "100GB initial",
            },
            "cache": {
                "type": "ElastiCache Redis",
                "cluster_mode": len(components) > 5,
                "memory": "2GB",
            },
            "storage": {
                "type": "S3",
                "versioning": True,
                "lifecycle": "Intelligent tiering",
            },
            "networking": {
                "vpc": "Dedicated VPC",
                "subnets": "Multi-AZ",
                "load_balancer": "Application Load Balancer",
            },
        }

    def _define_security_considerations(self, components: list[TechnicalComponent]) -> list[str]:
        """Define security considerations."""
        considerations = [
            "Implement JWT authentication with short-lived tokens",
            "Use HTTPS for all communications",
            "Encrypt sensitive data at rest",
            "Implement rate limiting and DDoS protection",
            "Regular security audits and penetration testing",
        ]
        
        # Component-specific considerations
        component_names = [c.name.lower() for c in components]
        
        if any("payment" in name for name in component_names):
            considerations.append("PCI DSS compliance for payment processing")
        
        if any("user" in name for name in component_names):
            considerations.append("GDPR compliance for user data")
        
        if any("api" in name for name in component_names):
            considerations.append("API security: input validation, CORS, CSP")
        
        return considerations

    def _create_scalability_plan(self, components: list[TechnicalComponent]) -> dict:
        """Create scalability plan."""
        return {
            "horizontal_scaling": {
                "strategy": "Auto-scaling based on CPU/memory",
                "min_instances": 2,
                "max_instances": 10,
                "scale_up_threshold": 70,
            },
            "vertical_scaling": {
                "strategy": "Upgrade instance types as needed",
                "monitoring": "Resource utilization metrics",
            },
            "database_scaling": {
                "read_replicas": True,
                "connection_pooling": True,
                "sharding_strategy": "By user ID",
            },
            "caching_strategy": {
                "layers": ["Application cache", "Database cache", "CDN"],
                "invalidation": "Event-driven",
                "ttl": "1 hour default",
            },
            "performance_targets": {
                "response_time": "< 200ms",
                "throughput": "1000 requests/second",
                "availability": "99.9%",
            },
        }

    def _define_monitoring_strategy(self, components: list[TechnicalComponent]) -> dict:
        """Define monitoring strategy."""
        return {
            "metrics": {
                "infrastructure": ["CPU", "Memory", "Disk", "Network"],
                "application": ["Response time", "Error rate", "Throughput"],
                "business": ["Active users", "Conversion rate", "Revenue"],
            },
            "logging": {
                "centralized": "ELK Stack",
                "retention": "30 days",
                "alerting": "Critical errors only",
            },
            "tracing": {
                "distributed_tracing": "Jaeger",
                "sampling_rate": "1%",
                "propagation": "W3C Trace Context",
            },
            "alerting": {
                "channels": ["Slack", "Email", "PagerDuty"],
                "escalation": "On-call rotation",
                "sla_breach": "Immediate alert",
            },
        }

    def _create_deployment_strategy(self, style: ArchitectureStyle) -> dict:
        """Create deployment strategy."""
        if style == ArchitectureStyle.MICROSERVICES:
            return {
                "strategy": "Blue-Green deployment",
                "rollback": "Automatic on health check failure",
                "canary": "10% traffic for 5 minutes",
                "ci_cd": "GitHub Actions + ArgoCD",
                "environments": ["dev", "staging", "production"],
            }
        else:
            return {
                "strategy": "Rolling deployment",
                "rollback": "Manual with automation",
                "ci_cd": "GitHub Actions",
                "environments": ["dev", "staging", "production"],
            }

    def _identify_technical_debt(self, components: list[TechnicalComponent]) -> list[str]:
        """Identify potential technical debt."""
        debt = []
        
        # Check component complexity
        high_effort_components = [c for c in components if c.estimated_effort > 30]
        if high_effort_components:
            debt.append(f"Complex components: {', '.join(c.name for c in high_effort_components[:3])}")
        
        # Check dependencies
        for comp in components:
            if len(comp.dependencies) > 3:
                debt.append(f"High dependencies in {comp.name}")
        
        # Common debt items
        debt.extend([
            "Lack of comprehensive test coverage",
            "Insufficient documentation",
            "Manual deployment processes",
        ])
        
        return debt[:5]

    def create_sprint_plan(self, plan_id: str, sprint_number: int) -> dict:
        """Create sprint plan from technical plan."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        # Distribute components across sprints
        sprint_capacity = 50  # story points per sprint
        current_sprint = []
        current_effort = 0
        
        for component in sorted(plan.components, key=lambda c: c.priority):
            if current_effort + component.estimated_effort <= sprint_capacity:
                current_sprint.append(component)
                current_effort += component.estimated_effort
        
        return {
            "sprint_number": sprint_number,
            "components": [c.to_dict() for c in current_sprint],
            "total_effort": current_effort,
            "capacity_used": current_effort / sprint_capacity * 100,
            "team_assignments": {c.team: c.name for c in current_sprint},
        }

    def get_engineering_insights(self) -> dict:
        """Get insights from engineering plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_components = sum(len(p.components) for p in all_plans)
        total_effort = sum(c.estimated_effort for p in all_plans for c in p.components)
        
        return {
            "total_plans": len(all_plans),
            "total_components": total_components,
            "total_effort": total_effort,
            "architecture_styles": list(set(p.architecture_style.value for p in all_plans)),
            "teams_involved": list(set(c.team for p in all_plans for c in p.components)),
        }