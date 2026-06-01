"""Frontend Team — Plan frontend development tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class FrontendTaskType(Enum):
    COMPONENT = "component"
    PAGE = "page"
    STATE_MANAGEMENT = "state_management"
    API_INTEGRATION = "api_integration"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    ACCESSIBILITY = "accessibility"


@dataclass
class FrontendTask:
    id: str = field(default_factory=lambda: f"FTASK-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: FrontendTaskType = FrontendTaskType.COMPONENT
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    component_library: str = ""
    dependencies: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    design_specs: dict = field(default_factory=dict)

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
class FrontendPlan:
    id: str = field(default_factory=lambda: f"FPLAN-{uuid.uuid4().hex[:8]}")
    framework: str = "React"
    tasks: list[FrontendTask] = field(default_factory=list)
    components: list[dict] = field(default_factory=list)
    pages: list[dict] = field(default_factory=list)
    state_management: dict = field(default_factory=dict)
    build_config: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "framework": self.framework,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "team_size": self.team_size,
            "components_count": len(self.components),
            "pages_count": len(self.pages),
        }


class FrontendTeam:
    """Plan and coordinate frontend development tasks."""

    def __init__(self):
        self.plans: dict[str, FrontendPlan] = {}
        self.tasks: dict[str, FrontendTask] = {}
        self.component_library: dict[str, dict] = {
            "buttons": ["PrimaryButton", "SecondaryButton", "IconButton", "ButtonGroup"],
            "forms": ["Input", "Select", "Checkbox", "Radio", "DatePicker", "Form"],
            "layout": ["Container", "Grid", "Stack", "Sidebar", "Header", "Footer"],
            "data_display": ["Table", "Card", "List", "Badge", "Avatar", "Tooltip"],
            "navigation": ["Navbar", "Tabs", "Breadcrumb", "Pagination", "Menu"],
            "feedback": ["Alert", "Toast", "Modal", "Spinner", "Progress", "Skeleton"],
        }

    def plan(self, design: dict, architecture: dict) -> FrontendPlan:
        """Plan frontend development based on design and architecture."""
        plan = FrontendPlan(
            framework=architecture.get("frontend_framework", "React"),
            team_size=architecture.get("frontend_team_size", 3),
        )
        
        # Create tasks based on design
        plan.tasks = self._create_tasks(design, architecture)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Create component list
        plan.components = self._create_components(design)
        
        # Create page list
        plan.pages = self._create_pages(design)
        
        # Plan state management
        plan.state_management = self._plan_state_management(architecture)
        
        # Configure build
        plan.build_config = self._configure_build(architecture)
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _create_tasks(self, design: dict, architecture: dict) -> list[FrontendTask]:
        """Create frontend tasks from design specs."""
        tasks = []
        
        # Component tasks
        component_tasks = [
            ("Button Components", FrontendTaskType.COMPONENT, 8),
            ("Form Components", FrontendTaskType.COMPONENT, 16),
            ("Layout Components", FrontendTaskType.COMPONENT, 12),
            ("Data Display Components", FrontendTaskType.COMPONENT, 20),
            ("Navigation Components", FrontendTaskType.COMPONENT, 12),
            ("Feedback Components", FrontendTaskType.COMPONENT, 16),
        ]
        
        for name, task_type, hours in component_tasks:
            task = FrontendTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                acceptance_criteria=[
                    "Component matches design specs",
                    "Responsive on all breakpoints",
                    "Accessible (WCAG 2.1 AA)",
                    "Unit tests written",
                ],
            )
            tasks.append(task)
        
        # Page tasks
        page_tasks = [
            ("Home Page", FrontendTaskType.PAGE, 24),
            ("Dashboard Page", FrontendTaskType.PAGE, 32),
            ("Settings Page", FrontendTaskType.PAGE, 20),
            ("Profile Page", FrontendTaskType.PAGE, 16),
            ("Login/Register Pages", FrontendTaskType.PAGE, 20),
        ]
        
        for name, task_type, hours in page_tasks:
            task = FrontendTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                acceptance_criteria=[
                    "Page matches design specs",
                    "Responsive on all breakpoints",
                    "Accessible (WCAG 2.1 AA)",
                    "Performance optimized",
                ],
            )
            tasks.append(task)
        
        # State management tasks
        state_tasks = [
            ("State Management Setup", FrontendTaskType.STATE_MANAGEMENT, 16),
            ("API Integration Layer", FrontendTaskType.API_INTEGRATION, 24),
            ("Error Handling", FrontendTaskType.COMPONENT, 12),
            ("Loading States", FrontendTaskType.COMPONENT, 8),
        ]
        
        for name, task_type, hours in state_tasks:
            task = FrontendTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Testing tasks
        testing_tasks = [
            ("Unit Tests", FrontendTaskType.TESTING, 24),
            ("Integration Tests", FrontendTaskType.TESTING, 32),
            ("E2E Tests", FrontendTaskType.TESTING, 40),
            ("Performance Testing", FrontendTaskType.OPTIMIZATION, 16),
            ("Accessibility Testing", FrontendTaskType.ACCESSIBILITY, 12),
        ]
        
        for name, task_type, hours in testing_tasks:
            task = FrontendTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        return tasks

    def _create_components(self, design: dict) -> list[dict]:
        """Create component specifications."""
        components = []
        
        for category, component_names in self.component_library.items():
            for comp_name in component_names:
                components.append({
                    "name": comp_name,
                    "category": category,
                    "variants": ["primary", "secondary", "disabled"],
                    "states": ["default", "hover", "active", "focus"],
                    "props": self._generate_component_props(comp_name),
                    "accessibility": self._generate_accessibility_requirements(comp_name),
                })
        
        return components

    def _generate_component_props(self, component_name: str) -> list[dict]:
        """Generate props for a component."""
        common_props = [
            {"name": "children", "type": "ReactNode", "required": True},
            {"name": "className", "type": "string", "required": False},
            {"name": "disabled", "type": "boolean", "required": False, "default": "false"},
        ]
        
        specific_props = {
            "Button": [
                {"name": "variant", "type": "primary | secondary | ghost", "required": False, "default": "primary"},
                {"name": "size", "type": "sm | md | lg", "required": False, "default": "md"},
                {"name": "onClick", "type": "() => void", "required": False},
            ],
            "Input": [
                {"name": "value", "type": "string", "required": True},
                {"name": "onChange", "type": "(value: string) => void", "required": True},
                {"name": "placeholder", "type": "string", "required": False},
                {"name": "type", "type": "text | password | email", "required": False, "default": "text"},
            ],
            "Modal": [
                {"name": "isOpen", "type": "boolean", "required": True},
                {"name": "onClose", "type": "() => void", "required": True},
                {"name": "title", "type": "string", "required": False},
            ],
        }
        
        return common_props + specific_props.get(component_name, [])

    def _generate_accessibility_requirements(self, component_name: str) -> dict:
        """Generate accessibility requirements for a component."""
        base_requirements = {
            "keyboard_navigation": True,
            "screen_reader_support": True,
            "focus_management": True,
        }
        
        specific_requirements = {
            "Button": {
                "aria_label": "Required when no text content",
                "role": "button",
                "keyboard": "Enter/Space to activate",
            },
            "Input": {
                "aria_label": "Required when no visible label",
                "role": "textbox",
                "keyboard": "Tab to navigate",
            },
            "Modal": {
                "aria_modal": "true",
                "role": "dialog",
                "keyboard": "Escape to close, Tab to cycle",
                "focus_trap": True,
            },
            "Table": {
                "role": "table",
                "aria_sortable": "For sortable columns",
                "keyboard": "Arrow keys for navigation",
            },
        }
        
        return {**base_requirements, **specific_requirements.get(component_name, {})}

    def _create_pages(self, design: dict) -> list[dict]:
        """Create page specifications."""
        pages = [
            {
                "name": "Home",
                "route": "/",
                "components": ["Header", "Hero", "Features", "Footer"],
                "layout": "full_width",
                "auth_required": False,
            },
            {
                "name": "Dashboard",
                "route": "/dashboard",
                "components": ["Header", "Sidebar", "Stats", "Charts", "Table"],
                "layout": "sidebar",
                "auth_required": True,
            },
            {
                "name": "Settings",
                "route": "/settings",
                "components": ["Header", "Sidebar", "Form", "Tabs"],
                "layout": "sidebar",
                "auth_required": True,
            },
            {
                "name": "Profile",
                "route": "/profile",
                "components": ["Header", "Avatar", "Form", "Activity"],
                "layout": "centered",
                "auth_required": True,
            },
            {
                "name": "Login",
                "route": "/login",
                "components": ["LoginForm", "SocialLogin"],
                "layout": "centered",
                "auth_required": False,
            },
            {
                "name": "Register",
                "route": "/register",
                "components": ["RegisterForm", "SocialLogin"],
                "layout": "centered",
                "auth_required": False,
            },
        ]
        
        # Add pages based on design
        if "products" in str(design).lower():
            pages.append({
                "name": "Products",
                "route": "/products",
                "components": ["Header", "ProductGrid", "Filters", "Pagination"],
                "layout": "full_width",
                "auth_required": False,
            })
        
        if "orders" in str(design).lower():
            pages.append({
                "name": "Orders",
                "route": "/orders",
                "components": ["Header", "Sidebar", "OrderList", "OrderDetail"],
                "layout": "sidebar",
                "auth_required": True,
            })
        
        return pages

    def _plan_state_management(self, architecture: dict) -> dict:
        """Plan state management approach."""
        return {
            "library": "Redux Toolkit",
            "patterns": {
                "global_state": "Redux store for app-wide state",
                "local_state": "React hooks for component state",
                "server_state": "React Query for API data",
            },
            "slices": [
                "authSlice - User authentication state",
                "uiSlice - UI preferences and theme",
                "dataSlice - Application data",
            ],
            "middleware": [
                "redux-thunk for async actions",
                "redux-persist for state persistence",
            ],
            "devtools": "Redux DevTools for development",
        }

    def _configure_build(self, architecture: dict) -> dict:
        """Configure build settings."""
        return {
            "bundler": "Vite",
            "transpiler": "TypeScript",
            "linter": "ESLint",
            "formatter": "Prettier",
            "testing": {
                "unit": "Vitest",
                "integration": "React Testing Library",
                "e2e": "Playwright",
            },
            "optimization": {
                "code_splitting": True,
                "tree_shaking": True,
                "lazy_loading": True,
                "image_optimization": True,
            },
            "ci_cd": {
                "linting": "ESLint check",
                "testing": "Unit and integration tests",
                "building": "Production build",
                "deployment": "Vercel/Netlify",
            },
        }

    def _create_sprint_plan(self, tasks: list[FrontendTask], team_size: int) -> list[dict]:
        """Create sprint plan for frontend tasks."""
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

    def get_component_coverage(self, plan_id: str) -> dict:
        """Get component coverage analysis."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        coverage = {
            "total_components": len(plan.components),
            "by_category": {},
            "accessibility_coverage": 0,
            "test_coverage": 0,
        }
        
        for component in plan.components:
            category = component["category"]
            if category not in coverage["by_category"]:
                coverage["by_category"][category] = 0
            coverage["by_category"][category] += 1
        
        # Calculate accessibility coverage
        components_with_a11y = sum(1 for c in plan.components if c.get("accessibility"))
        coverage["accessibility_coverage"] = components_with_a11y / len(plan.components) * 100 if plan.components else 0
        
        return coverage

    def get_frontend_insights(self) -> dict:
        """Get insights from frontend plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        total_components = sum(len(p.components) for p in all_plans)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "total_components": total_components,
            "frameworks_used": list(set(p.framework for p in all_plans)),
            "average_task_hours": total_hours / total_tasks if total_tasks > 0 else 0,
        }