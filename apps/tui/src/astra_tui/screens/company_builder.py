"""Company Builder Screen — Company building dashboard"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Company:
    id: str = ""
    name: str = ""
    description: str = ""
    industry: str = ""
    status: str = "founding"  # founding, growing, mature, pivoting, dissolved
    stage: str = "idea"  # idea, mvp, seed, series_a, series_b, ipo
    team_size: int = 0
    valuation: float = 0.0
    revenue: float = 0.0
    departments: list[str] = field(default_factory=list)
    key_metrics: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Department:
    id: str = ""
    company_id: str = ""
    name: str = ""
    head_count: int = 0
    budget: float = 0.0
    status: str = "active"
    goals: list[str] = field(default_factory=list)
    kpis: dict = field(default_factory=dict)


@dataclass
class Milestone:
    id: str = ""
    company_id: str = ""
    title: str = ""
    description: str = ""
    status: str = "pending"  # pending, achieved, missed
    target_date: Optional[str] = None
    achieved_date: Optional[str] = None


class CompanyBuilderScreen:
    """Company building dashboard screen."""

    TITLE = "Company Builder"

    def __init__(self):
        self.companies: dict[str, Company] = {}
        self.departments: dict[str, Department] = {}
        self.milestones: dict[str, Milestone] = {}
        self.selected_company_id: Optional[str] = None

    def create_company(self, name: str, description: str = "",
                       industry: str = "technology") -> Company:
        company_id = f"CO-{len(self.companies) + 1:04d}"
        company = Company(
            id=company_id,
            name=name,
            description=description,
            industry=industry,
        )
        self.companies[company_id] = company
        return company

    def add_department(self, company_id: str, name: str,
                       budget: float = 0.0) -> Optional[Department]:
        if company_id not in self.companies:
            return None
        dept_id = f"DEPT-{len(self.departments) + 1:04d}"
        dept = Department(
            id=dept_id,
            company_id=company_id,
            name=name,
            budget=budget,
        )
        self.departments[dept_id] = dept
        self.companies[company_id].departments.append(name)
        self.companies[company_id].team_size += 1
        return dept

    def add_milestone(self, company_id: str, title: str,
                      description: str = "", target_date: str = None) -> Optional[Milestone]:
        if company_id not in self.companies:
            return None
        ms_id = f"MS-{len(self.milestones) + 1:04d}"
        milestone = Milestone(
            id=ms_id,
            company_id=company_id,
            title=title,
            description=description,
            target_date=target_date,
        )
        self.milestones[ms_id] = milestone
        return milestone

    def achieve_milestone(self, milestone_id: str) -> Optional[Milestone]:
        milestone = self.milestones.get(milestone_id)
        if not milestone:
            return None
        milestone.status = "achieved"
        milestone.achieved_date = datetime.now(timezone.utc).isoformat()
        return milestone

    def update_company_stage(self, company_id: str, stage: str) -> Optional[Company]:
        company = self.companies.get(company_id)
        if not company:
            return None
        company.stage = stage
        return company

    def get_companies_by_stage(self, stage: str) -> list[Company]:
        return [c for c in self.companies.values() if c.stage == stage]

    def get_company_departments(self, company_id: str) -> list[Department]:
        return [d for d in self.departments.values() if d.company_id == company_id]

    def get_company_milestones(self, company_id: str) -> list[Milestone]:
        return [m for m in self.milestones.values() if m.company_id == company_id]

    def get_achieved_milestones(self, company_id: str) -> list[Milestone]:
        return [m for m in self.get_company_milestones(company_id) if m.status == "achieved"]

    def render_header(self) -> str:
        total = len(self.companies)
        stages = {}
        for c in self.companies.values():
            stages[c.stage] = stages.get(c.stage, 0) + 1
        stage_str = ", ".join(f"{k}:{v}" for k, v in stages.items())
        return f"╔══════════════════════════════════════════════════════════╗\n║ COMPANY BUILDER — {total} companies{'':<32}║\n║ Stages: {stage_str[:44]:<44} ║\n╚══════════════════════════════════════════════════════════╝"

    def render_companies(self) -> str:
        lines = ["┌─ Companies ─────────────────────────────────────────┐"]
        stage_icons = {"idea": "○", "mvp": "◐", "seed": "●", "series_a": "●●", "ipo": "★"}
        for c in list(self.companies.values())[:6]:
            icon = stage_icons.get(c.stage, "?")
            lines.append(f"│ {icon} {c.name[:20]:<20} {c.industry[:12]:<12} {c.stage:<10} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_milestones(self) -> str:
        lines = ["┌─ Recent Milestones ─────────────────────────────────┐"]
        for m in list(self.milestones.values())[:5]:
            status_icon = {"pending": "○", "achieved": "●", "missed": "✗"}.get(m.status, "?")
            lines.append(f"│ {status_icon} {m.title[:35]:<35} {m.status:<10} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_companies(),
            "",
            self.render_milestones(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        companies = list(self.companies.values())
        return {
            "total_companies": len(companies),
            "total_departments": len(self.departments),
            "total_milestones": len(self.milestones),
            "achieved_milestones": sum(1 for m in self.milestones.values() if m.status == "achieved"),
        }
