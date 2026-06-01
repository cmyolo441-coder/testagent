"""Security Team — Plan security tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class SecurityTaskType(Enum):
    SECURITY_ASSESSMENT = "security_assessment"
    VULNERABILITY_MANAGEMENT = "vulnerability_management"
    SECURITY_IMPLEMENTATION = "security_implementation"
    COMPLIANCE = "compliance"
    INCIDENT_RESPONSE = "incident_response"
    SECURITY_TRAINING = "security_training"


@dataclass
class SecurityTask:
    id: str = field(default_factory=lambda: f"SEC-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: SecurityTaskType = SecurityTaskType.SECURITY_ASSESSMENT
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    risk_level: str = "medium"
    compliance_frameworks: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
            "risk_level": self.risk_level,
        }


@dataclass
class SecurityPlan:
    id: str = field(default_factory=lambda: f"SECPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[SecurityTask] = field(default_factory=list)
    security_policy: dict = field(default_factory=dict)
    risk_assessment: dict = field(default_factory=dict)
    compliance_framework: dict = field(default_factory=dict)
    incident_response_plan: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "risk_level": self.risk_assessment.get("overall_risk", "unknown"),
        }


class SecurityTeam:
    """Plan and coordinate security tasks."""

    def __init__(self):
        self.plans: dict[str, SecurityPlan] = {}
        self.tasks: dict[str, SecurityTask] = {}

    def plan(self, security_plan: dict, requirements: list[str]) -> SecurityPlan:
        """Plan security activities based on security plan and requirements."""
        plan = SecurityPlan(
            team_size=security_plan.get("team_size", 2)
        )
        
        # Create tasks
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Define security policy
        plan.security_policy = self._define_security_policy(requirements)
        
        # Conduct risk assessment
        plan.risk_assessment = self._conduct_risk_assessment(requirements)
        
        # Set up compliance framework
        plan.compliance_framework = self._setup_compliance_framework(requirements)
        
        # Create incident response plan
        plan.incident_response_plan = self._create_incident_response_plan()
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[SecurityTask]:
        """Create security tasks from requirements."""
        tasks = []
        
        # Security Assessment tasks
        assessment_tasks = [
            ("Security Risk Assessment", SecurityTaskType.SECURITY_ASSESSMENT, 24, "high"),
            ("Threat Modeling", SecurityTaskType.SECURITY_ASSESSMENT, 16, "high"),
            ("Security Architecture Review", SecurityTaskType.SECURITY_ASSESSMENT, 20, "medium"),
        ]
        
        for name, task_type, hours, risk in assessment_tasks:
            task = SecurityTask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
                acceptance_criteria=[
                    "Assessment completed",
                    "Findings documented",
                    "Recommendations provided",
                ],
            )
            tasks.append(task)
        
        # Vulnerability Management tasks
        vuln_tasks = [
            ("Vulnerability Scanning", SecurityTaskType.VULNERABILITY_MANAGEMENT, 16, "high"),
            ("Penetration Testing", SecurityTaskType.VULNERABILITY_MANAGEMENT, 32, "critical"),
            ("Security Code Review", SecurityTaskType.VULNERABILITY_MANAGEMENT, 24, "high"),
            ("Dependency Vulnerability Check", SecurityTaskType.VULNERABILITY_MANAGEMENT, 8, "medium"),
        ]
        
        for name, task_type, hours, risk in vuln_tasks:
            task = SecurityTask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
            )
            tasks.append(task)
        
        # Security Implementation tasks
        impl_tasks = [
            ("Authentication System", SecurityTaskType.SECURITY_IMPLEMENTATION, 24, "high"),
            ("Authorization Framework", SecurityTaskType.SECURITY_IMPLEMENTATION, 20, "high"),
            ("Data Encryption", SecurityTaskType.SECURITY_IMPLEMENTATION, 16, "critical"),
            ("Security Logging", SecurityTaskType.SECURITY_IMPLEMENTATION, 12, "medium"),
        ]
        
        for name, task_type, hours, risk in impl_tasks:
            task = SecurityTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
            )
            tasks.append(task)
        
        # Compliance tasks
        compliance_tasks = [
            ("GDPR Compliance", SecurityTaskType.COMPLIANCE, 20, "high", ["GDPR"]),
            ("SOC 2 Compliance", SecurityTaskType.COMPLIANCE, 32, "high", ["SOC2"]),
            ("HIPAA Compliance", SecurityTaskType.COMPLIANCE, 24, "critical", ["HIPAA"]),
            ("PCI DSS Compliance", SecurityTaskType.COMPLIANCE, 28, "critical", ["PCI"]),
        ]
        
        for name, task_type, hours, risk, frameworks in compliance_tasks:
            task = SecurityTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
                compliance_frameworks=frameworks,
            )
            tasks.append(task)
        
        # Incident Response tasks
        incident_tasks = [
            ("Incident Response Plan", SecurityTaskType.INCIDENT_RESPONSE, 16, "high"),
            ("Security Monitoring Setup", SecurityTaskType.INCIDENT_RESPONSE, 20, "high"),
            ("Disaster Recovery Plan", SecurityTaskType.INCIDENT_RESPONSE, 24, "critical"),
        ]
        
        for name, task_type, hours, risk in incident_tasks:
            task = SecurityTask(
                name=name,
                description=f"Create {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
            )
            tasks.append(task)
        
        # Security Training tasks
        training_tasks = [
            ("Security Awareness Training", SecurityTaskType.SECURITY_TRAINING, 8, "medium"),
            ("Developer Security Training", SecurityTaskType.SECURITY_TRAINING, 12, "medium"),
            ("Incident Response Drills", SecurityTaskType.SECURITY_TRAINING, 8, "medium"),
        ]
        
        for name, task_type, hours, risk in training_tasks:
            task = SecurityTask(
                name=name,
                description=f"Conduct {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                risk_level=risk,
            )
            tasks.append(task)
        
        return tasks

    def _define_security_policy(self, requirements: list[str]) -> dict:
        """Define security policy."""
        return {
            "access_control": {
                "principle": "Least privilege",
                "authentication": "Multi-factor authentication required",
                "authorization": "Role-based access control (RBAC)",
                "session_management": "Secure session handling with timeout",
            },
            "data_protection": {
                "encryption_at_rest": "AES-256",
                "encryption_in_transit": "TLS 1.3",
                "key_management": "Hardware security modules (HSM)",
                "data_classification": ["Public", "Internal", "Confidential", "Restricted"],
            },
            "network_security": {
                "firewall": "Web application firewall (WAF)",
                "ddos_protection": "DDoS mitigation service",
                "vpn": "Required for remote access",
                "network_segmentation": "Isolate sensitive systems",
            },
            "application_security": {
                "secure_development": "OWASP guidelines",
                "code_review": "Security-focused code review",
                "dependency_scanning": "Automated dependency checks",
                "static_analysis": "SAST tools integrated in CI/CD",
            },
            "monitoring_and_logging": {
                "security_events": "Centralized security logging",
                "intrusion_detection": "IDS/IPS systems",
                "SIEM": "Security information and event management",
                "audit_trails": "Comprehensive audit logging",
            },
        }

    def _conduct_risk_assessment(self, requirements: list[str]) -> dict:
        """Conduct risk assessment."""
        return {
            "risk_categories": {
                "technical": {
                    "vulnerabilities": "Medium risk - regular scanning required",
                    "misconfigurations": "High risk - infrastructure as code",
                    "outdated_components": "Medium risk - automated updates",
                },
                "operational": {
                    "insider_threats": "Low risk - access controls",
                    "human_error": "Medium risk - training required",
                    "process_gaps": "Medium risk - regular audits",
                },
                "compliance": {
                    "regulatory": "High risk - strict requirements",
                    "industry_standards": "Medium risk - best practices",
                    "contractual": "Low risk - clear requirements",
                },
            },
            "overall_risk": "Medium",
            "risk_score": 5.5,
            "mitigation_strategies": [
                "Implement defense in depth",
                "Regular security assessments",
                "Security awareness training",
                "Automated security testing",
            ],
        }

    def _setup_compliance_framework(self, requirements: list[str]) -> dict:
        """Set up compliance framework."""
        return {
            "frameworks": {
                "GDPR": {
                    "scope": "User data processing",
                    "requirements": ["Data minimization", "Right to erasure", "Consent management"],
                    "controls": ["Data encryption", "Access logging", "Privacy by design"],
                },
                "SOC2": {
                    "scope": "Service organization controls",
                    "requirements": ["Security", "Availability", "Processing integrity"],
                    "controls": ["Access controls", "Change management", "Incident response"],
                },
                "ISO27001": {
                    "scope": "Information security management",
                    "requirements": ["Risk management", "Security controls", "Continuous improvement"],
                    "controls": ["ISMS implementation", "Internal audits", "Management review"],
                },
            },
            "audit_schedule": {
                "internal_audits": "Quarterly",
                "external_audits": "Annually",
                "penetration_testing": "Bi-annually",
            },
            "compliance_monitoring": {
                "automated_checks": "Continuous",
                "manual_reviews": "Monthly",
                "reporting": "Quarterly to management",
            },
        }

    def _create_incident_response_plan(self) -> dict:
        """Create incident response plan."""
        return {
            "incident_categories": {
                "security_breach": {
                    "severity": "Critical",
                    "response_time": "1 hour",
                    "escalation": "Immediate to CISO",
                },
                "data_leak": {
                    "severity": "Critical",
                    "response_time": "2 hours",
                    "escalation": "Legal and management",
                },
                "malware": {
                    "severity": "High",
                    "response_time": "4 hours",
                    "escalation": "Security team lead",
                },
                "phishing": {
                    "severity": "Medium",
                    "response_time": "24 hours",
                    "escalation": "Security team",
                },
            },
            "response_procedures": {
                "detection": "Identify and classify incident",
                "containment": "Limit damage and preserve evidence",
                "eradication": "Remove threat and fix vulnerabilities",
                "recovery": "Restore systems and operations",
                "lessons_learned": "Document and improve processes",
            },
            "communication_plan": {
                "internal": "Security team → Management → All employees",
                "external": "Legal → Regulators → Affected parties",
                "public": "PR team → Public statement if required",
            },
            "recovery_objectives": {
                "rto": "4 hours (Recovery Time Objective)",
                "rpo": "1 hour (Recovery Point Objective)",
                "backup_strategy": "3-2-1 rule (3 copies, 2 media, 1 offsite)",
            },
        }

    def _create_sprint_plan(self, tasks: list[SecurityTask], team_size: int) -> list[dict]:
        """Create sprint plan for security tasks."""
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

    def get_security_posture(self, plan_id: str) -> dict:
        """Get security posture assessment."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        completed_tasks = [t for t in plan.tasks if t.status == "completed"]
        critical_tasks = [t for t in plan.tasks if t.risk_level == "critical"]
        
        return {
            "tasks_completed": len(completed_tasks),
            "tasks_total": len(plan.tasks),
            "completion_rate": len(completed_tasks) / len(plan.tasks) * 100 if plan.tasks else 0,
            "critical_tasks_remaining": len([t for t in critical_tasks if t.status != "completed"]),
            "risk_level": plan.risk_assessment.get("overall_risk", "unknown"),
            "compliance_status": self._get_compliance_status(plan),
        }

    def _get_compliance_status(self, plan: SecurityPlan) -> dict:
        """Get compliance status."""
        compliance_tasks = [t for t in plan.tasks if t.task_type == SecurityTaskType.COMPLIANCE]
        completed_compliance = [t for t in compliance_tasks if t.status == "completed"]
        
        return {
            "frameworks": plan.compliance_framework.get("frameworks", {}).keys(),
            "completion_rate": len(completed_compliance) / len(compliance_tasks) * 100 if compliance_tasks else 0,
            "next_audit": "2024-01-01",
        }

    def get_security_insights(self) -> dict:
        """Get insights from security plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        critical_tasks = sum(1 for p in all_plans for t in p.tasks if t.risk_level == "critical")
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "critical_tasks": critical_tasks,
            "risk_levels": self._count_risk_levels(all_plans),
        }

    def _count_risk_levels(self, plans: list[SecurityPlan]) -> dict:
        """Count tasks by risk level."""
        risk_counts = {}
        for plan in plans:
            for task in plan.tasks:
                risk = task.risk_level
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
        return risk_counts