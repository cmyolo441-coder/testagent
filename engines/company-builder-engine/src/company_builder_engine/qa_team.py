"""QA Team — Plan quality assurance tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class QATaskType(Enum):
    TEST_PLANNING = "test_planning"
    TEST_AUTOMATION = "test_automation"
    MANUAL_TESTING = "manual_testing"
    PERFORMANCE_TESTING = "performance_testing"
    SECURITY_TESTING = "security_testing"
    USABILITY_TESTING = "usability_testing"


@dataclass
class QATask:
    id: str = field(default_factory=lambda: f"QATASK-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: QATaskType = QATaskType.TEST_PLANNING
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    test_cases: list[dict] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
            "test_cases_count": len(self.test_cases),
        }


@dataclass
class QAPlan:
    id: str = field(default_factory=lambda: f"QAPLAN-{uuid.uuid4().hex[:8]}")
    tasks: list[QATask] = field(default_factory=list)
    test_strategy: dict = field(default_factory=dict)
    test_environment: dict = field(default_factory=dict)
    test_data: dict = field(default_factory=dict)
    quality_metrics: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "test_cases_count": sum(len(t.test_cases) for t in self.tasks),
        }


class QATeam:
    """Plan and coordinate quality assurance tasks."""

    def __init__(self):
        self.plans: dict[str, QAPlan] = {}
        self.tasks: dict[str, QATask] = {}

    def plan(self, test_plan: dict, requirements: list[str]) -> QAPlan:
        """Plan QA activities based on test plan and requirements."""
        plan = QAPlan(
            team_size=test_plan.get("team_size", 3)
        )
        
        # Create tasks
        plan.tasks = self._create_tasks(requirements)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Define test strategy
        plan.test_strategy = self._define_test_strategy(requirements)
        
        # Set up test environment
        plan.test_environment = self._setup_test_environment()
        
        # Plan test data
        plan.test_data = self._plan_test_data(requirements)
        
        # Define quality metrics
        plan.quality_metrics = self._define_quality_metrics()
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, requirements: list[str]) -> list[QATask]:
        """Create QA tasks from requirements."""
        tasks = []
        
        # Test Planning tasks
        planning_tasks = [
            ("Test Strategy Document", QATaskType.TEST_PLANNING, 16),
            ("Test Case Development", QATaskType.TEST_PLANNING, 40),
            ("Test Data Preparation", QATaskType.TEST_PLANNING, 20),
        ]
        
        for name, task_type, hours in planning_tasks:
            task = QATask(
                name=name,
                description=f"Create {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                acceptance_criteria=[
                    "Documentation complete",
                    "Reviewed by team",
                    "Approved by stakeholders",
                ],
            )
            tasks.append(task)
        
        # Test Automation tasks
        automation_tasks = [
            ("Unit Test Automation", QATaskType.TEST_AUTOMATION, 32),
            ("Integration Test Automation", QATaskType.TEST_AUTOMATION, 40),
            ("E2E Test Automation", QATaskType.TEST_AUTOMATION, 48),
            ("API Test Automation", QATaskType.TEST_AUTOMATION, 24),
        ]
        
        for name, task_type, hours in automation_tasks:
            task = QATask(
                name=name,
                description=f"Automate {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                test_cases=[
                    {"name": f"Test {name} scenario 1", "steps": [], "expected": "Pass"},
                    {"name": f"Test {name} scenario 2", "steps": [], "expected": "Pass"},
                ],
            )
            tasks.append(task)
        
        # Manual Testing tasks
        manual_tasks = [
            ("Exploratory Testing", QATaskType.MANUAL_TESTING, 24),
            ("User Acceptance Testing", QATaskType.MANUAL_TESTING, 32),
            ("Cross-browser Testing", QATaskType.MANUAL_TESTING, 20),
            ("Mobile Device Testing", QATaskType.MANUAL_TESTING, 24),
        ]
        
        for name, task_type, hours in manual_tasks:
            task = QATask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Performance Testing tasks
        performance_tasks = [
            ("Load Testing", QATaskType.PERFORMANCE_TESTING, 24),
            ("Stress Testing", QATaskType.PERFORMANCE_TESTING, 20),
            ("Endurance Testing", QATaskType.PERFORMANCE_TESTING, 16),
            ("Spike Testing", QATaskType.PERFORMANCE_TESTING, 12),
        ]
        
        for name, task_type, hours in performance_tasks:
            task = QATask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Security Testing tasks
        security_tasks = [
            ("Vulnerability Scanning", QATaskType.SECURITY_TESTING, 16),
            ("Penetration Testing", QATaskType.SECURITY_TESTING, 32),
            ("Security Code Review", QATaskType.SECURITY_TESTING, 24),
        ]
        
        for name, task_type, hours in security_tasks:
            task = QATask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Usability Testing tasks
        usability_tasks = [
            ("Usability Test Planning", QATaskType.USABILITY_TESTING, 16),
            ("Usability Test Execution", QATaskType.USABILITY_TESTING, 24),
            ("Accessibility Testing", QATaskType.USABILITY_TESTING, 20),
        ]
        
        for name, task_type, hours in usability_tasks:
            task = QATask(
                name=name,
                description=f"Perform {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        return tasks

    def _define_test_strategy(self, requirements: list[str]) -> dict:
        """Define comprehensive test strategy."""
        return {
            "testing_levels": {
                "unit": {
                    "coverage_target": 80,
                    "tools": ["Jest", "PyTest"],
                    "automation": "100%",
                },
                "integration": {
                    "coverage_target": 70,
                    "tools": ["React Testing Library", "Supertest"],
                    "automation": "90%",
                },
                "e2e": {
                    "coverage_target": 60,
                    "tools": ["Playwright", "Cypress"],
                    "automation": "80%",
                },
                "performance": {
                    "targets": {
                        "response_time": "< 200ms",
                        "throughput": "1000 req/s",
                        "error_rate": "< 1%",
                    },
                    "tools": ["k6", "JMeter"],
                },
                "security": {
                    "frequency": "Weekly scans, Quarterly pen tests",
                    "tools": ["Snyk", "OWASP ZAP"],
                },
            },
            "test_environment_strategy": {
                "development": "Unit and integration tests",
                "staging": "E2E and performance tests",
                "production": "Monitoring and canary releases",
            },
            "defect_management": {
                "severity_levels": ["Critical", "High", "Medium", "Low"],
                "resolution_targets": {
                    "Critical": "24 hours",
                    "High": "3 days",
                    "Medium": "1 week",
                    "Low": "Next sprint",
                },
            },
        }

    def _setup_test_environment(self) -> dict:
        """Set up test environment configuration."""
        return {
            "environments": {
                "development": {
                    "purpose": "Unit and integration testing",
                    "data": "Synthetic test data",
                    "availability": "Always available",
                },
                "staging": {
                    "purpose": "E2E, performance, and UAT testing",
                    "data": "Anonymized production data",
                    "availability": "Business hours",
                },
                "production": {
                    "purpose": "Canary releases and monitoring",
                    "data": "Real user data",
                    "availability": "24/7",
                },
            },
            "test_data_management": {
                "strategy": "Synthetic data with production-like patterns",
                "refresh_frequency": "Weekly",
                "data_privacy": "GDPR compliant anonymization",
            },
            "test_tools": {
                "automation": ["Playwright", "Jest", "React Testing Library"],
                "performance": ["k6", "JMeter"],
                "security": ["Snyk", "OWASP ZAP"],
                "api": ["Postman", "Insomnia"],
            },
        }

    def _plan_test_data(self, requirements: list[str]) -> dict:
        """Plan test data management."""
        return {
            "data_types": {
                "user_data": {
                    "volume": "1000 users",
                    "varieties": ["Admin", "Regular", "Inactive"],
                    "generation": "Faker library",
                },
                "product_data": {
                    "volume": "5000 products",
                    "varieties": ["Active", "Out of stock", "Discontinued"],
                    "generation": "Custom script",
                },
                "transaction_data": {
                    "volume": "50000 transactions",
                    "varieties": ["Successful", "Failed", "Pending"],
                    "generation": "Historical data",
                },
            },
            "data_management": {
                "storage": "Dedicated test database",
                "refresh": "Before each test cycle",
                "cleanup": "Automated after tests",
            },
            "data_privacy": {
                "anonymization": "All PII anonymized",
                "compliance": ["GDPR", "CCPA"],
                "retention": "30 days",
            },
        }

    def _define_quality_metrics(self) -> dict:
        """Define quality metrics and KPIs."""
        return {
            "code_quality": {
                "metrics": ["Code coverage", "Code complexity", "Technical debt"],
                "targets": {
                    "code_coverage": "> 80%",
                    "complexity": "< 10 per function",
                    "debt_ratio": "< 5%",
                },
            },
            "test_effectiveness": {
                "metrics": ["Test pass rate", "Defect detection rate", "Test execution time"],
                "targets": {
                    "pass_rate": "> 95%",
                    "detection_rate": "> 90%",
                    "execution_time": "< 30 minutes",
                },
            },
            "defect_metrics": {
                "metrics": ["Defect density", "Defect leakage", "Mean time to detect"],
                "targets": {
                    "density": "< 1 defect per 1000 lines",
                    "leakage": "< 5% to production",
                    "mttd": "< 1 hour",
                },
            },
            "customer_satisfaction": {
                "metrics": ["NPS", "CSAT", "Defect escape rate"],
                "targets": {
                    "nps": "> 50",
                    "csat": "> 4.5/5",
                    "escape_rate": "< 2%",
                },
            },
        }

    def _create_sprint_plan(self, tasks: list[QATask], team_size: int) -> list[dict]:
        """Create sprint plan for QA tasks."""
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

    def get_test_coverage_report(self, plan_id: str) -> dict:
        """Get test coverage report."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        total_test_cases = sum(len(t.test_cases) for t in plan.tasks)
        
        return {
            "total_test_cases": total_test_cases,
            "by_type": self._count_tasks_by_type(plan.tasks),
            "automation_coverage": self._calculate_automation_coverage(plan.tasks),
            "estimated_execution_time": total_test_cases * 5,  # 5 minutes per test case
        }

    def _count_tasks_by_type(self, tasks: list[QATask]) -> dict:
        """Count tasks by type."""
        type_counts = {}
        for task in tasks:
            task_type = task.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        return type_counts

    def _calculate_automation_coverage(self, tasks: list[QATask]) -> float:
        """Calculate automation coverage."""
        automated_tasks = [t for t in tasks if t.task_type == QATaskType.TEST_AUTOMATION]
        total_hours = sum(t.estimated_hours for t in tasks)
        automated_hours = sum(t.estimated_hours for t in automated_tasks)
        
        return automated_hours / total_hours * 100 if total_hours > 0 else 0

    def get_qa_insights(self) -> dict:
        """Get insights from QA plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        total_test_cases = sum(len(t.test_cases) for p in all_plans for t in p.tasks)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "total_test_cases": total_test_cases,
            "average_test_cases_per_task": total_test_cases / total_tasks if total_tasks > 0 else 0,
        }