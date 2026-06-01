"""Mobile Team — Plan mobile development tasks"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class MobilePlatform(Enum):
    IOS = "ios"
    ANDROID = "android"
    CROSS_PLATFORM = "cross_platform"


class MobileTaskType(Enum):
    UI_IMPLEMENTATION = "ui_implementation"
    NAVIGATION = "navigation"
    API_INTEGRATION = "api_integration"
    LOCAL_STORAGE = "local_storage"
    PUSH_NOTIFICATIONS = "push_notifications"
    PERFORMANCE = "performance"
    TESTING = "testing"
    APP_STORE = "app_store"


@dataclass
class MobileTask:
    id: str = field(default_factory=lambda: f"MTASK-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    task_type: MobileTaskType = MobileTaskType.UI_IMPLEMENTATION
    platform: MobilePlatform = MobilePlatform.CROSS_PLATFORM
    priority: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    status: str = "todo"
    assigned_to: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    platform_specific: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.task_type.value,
            "platform": self.platform.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "status": self.status,
        }


@dataclass
class MobilePlan:
    id: str = field(default_factory=lambda: f"MPLAN-{uuid.uuid4().hex[:8]}")
    platform: MobilePlatform = MobilePlatform.CROSS_PLATFORM
    framework: str = "React Native"
    tasks: list[MobileTask] = field(default_factory=list)
    screens: list[dict] = field(default_factory=list)
    navigation_structure: dict = field(default_factory=dict)
    offline_support: dict = field(default_factory=dict)
    push_notification_config: dict = field(default_factory=dict)
    app_store_config: dict = field(default_factory=dict)
    estimated_total_hours: float = 0
    team_size: int = 0
    sprint_plan: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "framework": self.framework,
            "tasks_count": len(self.tasks),
            "total_hours": self.estimated_total_hours,
            "screens_count": len(self.screens),
        }


class MobileTeam:
    """Plan and coordinate mobile development tasks."""

    def __init__(self):
        self.plans: dict[str, MobilePlan] = {}
        self.tasks: dict[str, MobileTask] = {}
        self.screen_templates: dict[str, list[str]] = {
            "auth": ["Login", "Register", "Forgot Password", "Onboarding"],
            "main": ["Home", "Dashboard", "Profile", "Settings"],
            "content": ["List", "Detail", "Search", "Filter"],
            "media": ["Camera", "Gallery", "Video Player", "Audio Player"],
            "social": ["Chat", "Notifications", "Social Feed", "User Profile"],
        }

    def plan(self, strategy: dict, architecture: dict) -> MobilePlan:
        """Plan mobile development based on strategy and architecture."""
        plan = MobilePlan(
            platform=self._determine_platform(strategy),
            framework=architecture.get("mobile_framework", "React Native"),
            team_size=architecture.get("mobile_team_size", 3),
        )
        
        # Create tasks
        plan.tasks = self._create_tasks(strategy, plan.platform)
        for task in plan.tasks:
            self.tasks[task.id] = task
        
        # Create screens
        plan.screens = self._create_screens(strategy)
        
        # Plan navigation
        plan.navigation_structure = self._plan_navigation(strategy)
        
        # Plan offline support
        plan.offline_support = self._plan_offline_support(strategy)
        
        # Configure push notifications
        plan.push_notification_config = self._configure_push_notifications(strategy)
        
        # Configure app store
        plan.app_store_config = self._configure_app_store(plan.platform)
        
        # Calculate estimated hours
        plan.estimated_total_hours = sum(t.estimated_hours for t in plan.tasks)
        
        # Create sprint plan
        plan.sprint_plan = self._create_sprint_plan(plan.tasks, plan.team_size)
        
        self.plans[plan.id] = plan
        return plan

    def _determine_platform(self, strategy: dict) -> MobilePlatform:
        """Determine target platform based on strategy."""
        target_market = strategy.get("target_market", "general")
        
        if "ios" in target_market.lower():
            return MobilePlatform.IOS
        elif "android" in target_market.lower():
            return MobilePlatform.ANDROID
        else:
            return MobilePlatform.CROSS_PLATFORM

    def _create_tasks(self, strategy: dict, platform: MobilePlatform) -> list[MobileTask]:
        """Create mobile development tasks."""
        tasks = []
        
        # UI Implementation tasks
        ui_tasks = [
            ("Screen Navigation", MobileTaskType.NAVIGATION, 24),
            ("Form Components", MobileTaskType.UI_IMPLEMENTATION, 20),
            ("List Components", MobileTaskType.UI_IMPLEMENTATION, 16),
            ("Modal Components", MobileTaskType.UI_IMPLEMENTATION, 12),
            ("Animation Effects", MobileTaskType.UI_IMPLEMENTATION, 16),
        ]
        
        for name, task_type, hours in ui_tasks:
            task = MobileTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                platform=platform,
                priority=len(tasks) + 1,
                estimated_hours=hours,
                acceptance_criteria=[
                    "Works on target platform(s)",
                    "Follows platform guidelines",
                    "Responsive to different screen sizes",
                    "Accessible",
                ],
            )
            tasks.append(task)
        
        # API Integration tasks
        api_tasks = [
            ("API Client Setup", MobileTaskType.API_INTEGRATION, 16),
            ("Data Caching", MobileTaskType.LOCAL_STORAGE, 12),
            ("Offline Support", MobileTaskType.LOCAL_STORAGE, 20),
            ("Push Notifications", MobileTaskType.PUSH_NOTIFICATIONS, 24),
        ]
        
        for name, task_type, hours in api_tasks:
            task = MobileTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                platform=platform,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Performance tasks
        performance_tasks = [
            ("Performance Optimization", MobileTaskType.PERFORMANCE, 20),
            ("App Size Optimization", MobileTaskType.PERFORMANCE, 12),
            ("Battery Optimization", MobileTaskType.PERFORMANCE, 16),
        ]
        
        for name, task_type, hours in performance_tasks:
            task = MobileTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                platform=platform,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # Testing tasks
        testing_tasks = [
            ("Unit Tests", MobileTaskType.TESTING, 24),
            ("Integration Tests", MobileTaskType.TESTING, 32),
            ("UI Tests", MobileTaskType.TESTING, 40),
            ("Performance Tests", MobileTaskType.TESTING, 16),
        ]
        
        for name, task_type, hours in testing_tasks:
            task = MobileTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                platform=platform,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        # App Store tasks
        app_store_tasks = [
            ("iOS App Store Submission", MobileTaskType.APP_STORE, 8),
            ("Google Play Store Submission", MobileTaskType.APP_STORE, 8),
        ]
        
        for name, task_type, hours in app_store_tasks:
            task = MobileTask(
                name=name,
                description=f"Implement {name.lower()}",
                task_type=task_type,
                platform=platform,
                priority=len(tasks) + 1,
                estimated_hours=hours,
            )
            tasks.append(task)
        
        return tasks

    def _create_screens(self, strategy: dict) -> list[dict]:
        """Create mobile screen specifications."""
        screens = []
        
        # Authentication screens
        for screen_name in self.screen_templates["auth"]:
            screens.append({
                "name": screen_name,
                "route": f"/{screen_name.lower().replace(' ', '-')}",
                "components": ["TextInput", "Button", "Header"],
                "auth_required": False,
                "platform_specific": {
                    "ios": "Native navigation",
                    "android": "Material Design",
                },
            })
        
        # Main screens
        for screen_name in self.screen_templates["main"]:
            screens.append({
                "name": screen_name,
                "route": f"/{screen_name.lower()}",
                "components": ["Header", "Content", "TabBar"],
                "auth_required": True,
                "platform_specific": {
                    "ios": "Tab bar navigation",
                    "android": "Bottom navigation",
                },
            })
        
        # Content screens
        for screen_name in self.screen_templates["content"]:
            screens.append({
                "name": screen_name,
                "route": f"/{screen_name.lower()}",
                "components": ["Header", "List", "SearchBar"],
                "auth_required": True,
            })
        
        return screens

    def _plan_navigation(self, strategy: dict) -> dict:
        """Plan navigation structure."""
        return {
            "library": "React Navigation",
            "structure": {
                "auth_stack": ["Login", "Register", "ForgotPassword"],
                "main_stack": ["Home", "Dashboard", "Profile", "Settings"],
                "modal_stack": ["ImageViewer", "WebView", "Scanner"],
            },
            "deep_linking": {
                "enabled": True,
                "schemes": ["myapp://"],
                "prefixes": ["https://myapp.com"],
            },
            "navigation_patterns": {
                "tab_navigation": "Main app sections",
                "stack_navigation": "Screen flow within sections",
                "modal_navigation": "Temporary screens",
            },
        }

    def _plan_offline_support(self, strategy: dict) -> dict:
        """Plan offline support."""
        return {
            "strategy": "Progressive Web App (PWA) with native offline support",
            "storage": {
                "local": "AsyncStorage",
                "database": "SQLite",
                "cache": "React Query cache",
            },
            "sync_strategy": {
                "background_sync": True,
                "conflict_resolution": "Last write wins",
                "retry_policy": "Exponential backoff",
            },
            "offline_features": [
                "View cached data",
                "Queue actions for sync",
                "Read previously loaded content",
            ],
            "connectivity_detection": {
                "library": "@react-native-community/netinfo",
                "fallback_ui": "Offline banner",
            },
        }

    def _configure_push_notifications(self, strategy: dict) -> dict:
        """Configure push notifications."""
        return {
            "provider": "Firebase Cloud Messaging (FCM)",
            "ios_config": {
                "apns_key": "Path to APNS key",
                "team_id": "Apple Developer Team ID",
                "bundle_id": "com.company.app",
            },
            "android_config": {
                "google_services_json": "Path to google-services.json",
                "channel_id": "default",
                "channel_name": "General notifications",
            },
            "notification_types": [
                {"type": "promotional", "priority": "normal"},
                {"type": "transactional", "priority": "high"},
                {"type": "social", "priority": "normal"},
            ],
            "deep_linking": {
                "enabled": True,
                "scheme": "myapp://notification",
            },
        }

    def _configure_app_store(self, platform: MobilePlatform) -> dict:
        """Configure app store settings."""
        if platform == MobilePlatform.IOS:
            return {
                "store": "App Store",
                "bundle_id": "com.company.app",
                "team_id": "Apple Developer Team ID",
                "app_privacy_url": "https://myapp.com/privacy",
                "support_url": "https://myapp.com/support",
                "marketing_url": "https://myapp.com",
                "categories": ["Business", "Productivity"],
                "age_rating": "4+",
                "pricing": "Free",
                "in_app_purchases": True,
            }
        elif platform == MobilePlatform.ANDROID:
            return {
                "store": "Google Play Store",
                "package_name": "com.company.app",
                "service_account_json": "Path to service account JSON",
                "privacy_policy_url": "https://myapp.com/privacy",
                "support_email": "support@myapp.com",
                "categories": ["Business", "Productivity"],
                "content_rating": "Everyone",
                "pricing": "Free",
                "in_app_products": True,
            }
        else:
            return {
                "stores": ["App Store", "Google Play Store"],
                "shared_config": {
                    "app_name": "My App",
                    "description": "A amazing mobile application",
                    "keywords": ["productivity", "business", "tools"],
                    "screenshots": [],
                    "preview_videos": [],
                },
            }

    def _create_sprint_plan(self, tasks: list[MobileTask], team_size: int) -> list[dict]:
        """Create sprint plan for mobile tasks."""
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

    def get_platform_coverage(self, plan_id: str) -> dict:
        """Get platform coverage analysis."""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        coverage = {
            "target_platform": plan.platform.value,
            "screens_count": len(plan.screens),
            "offline_support": plan.offline_support.get("strategy", "None"),
            "push_notifications": plan.push_notification_config.get("provider", "None"),
            "app_store_ready": bool(plan.app_store_config),
        }
        
        return coverage

    def get_mobile_insights(self) -> dict:
        """Get insights from mobile plans."""
        all_plans = list(self.plans.values())
        
        if not all_plans:
            return {"status": "no_plans"}
        
        total_tasks = sum(len(p.tasks) for p in all_plans)
        total_hours = sum(t.estimated_hours for p in all_plans for t in p.tasks)
        total_screens = sum(len(p.screens) for p in all_plans)
        
        return {
            "total_plans": len(all_plans),
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "total_screens": total_screens,
            "platforms_covered": list(set(p.platform.value for p in all_plans)),
            "frameworks_used": list(set(p.framework for p in all_plans)),
        }