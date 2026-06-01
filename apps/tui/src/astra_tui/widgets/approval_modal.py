"""Approval Modal Widget — Approval dialog for risky operations"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ApprovalItem:
    id: str = ""
    title: str = ""
    description: str = ""
    risk_level: str = "medium"
    risk_score: float = 0.5
    conditions: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected, expired
    approver: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: Optional[str] = None


class ApprovalModal:
    """Approval dialog widget for risky operations."""

    def __init__(self):
        self.items: list[ApprovalItem] = []
        self.selected_index: int = 0
        self.is_visible: bool = False
        self.modal_title: str = "Approval Required"

    def show(self, title: str, description: str = "",
             risk_level: str = "medium", risk_score: float = 0.5,
             conditions: list[str] = None, context: dict = None) -> ApprovalItem:
        item = ApprovalItem(
            id=f"APR-{len(self.items) + 1:04d}",
            title=title,
            description=description,
            risk_level=risk_level,
            risk_score=risk_score,
            conditions=conditions or [],
            context=context or {},
        )
        self.items.append(item)
        self.is_visible = True
        return item

    def approve(self, item_id: str = None, approver: str = "",
                notes: str = "") -> Optional[ApprovalItem]:
        target_id = item_id or (self.items[-1].id if self.items else None)
        if not target_id:
            return None
        for item in self.items:
            if item.id == target_id and item.status == "pending":
                item.status = "approved"
                item.approver = approver
                item.notes = notes
                item.decided_at = datetime.now(timezone.utc).isoformat()
                self.is_visible = False
                return item
        return None

    def reject(self, item_id: str = None, approver: str = "",
               notes: str = "") -> Optional[ApprovalItem]:
        target_id = item_id or (self.items[-1].id if self.items else None)
        if not target_id:
            return None
        for item in self.items:
            if item.id == target_id and item.status == "pending":
                item.status = "rejected"
                item.approver = approver
                item.notes = notes
                item.decided_at = datetime.now(timezone.utc).isoformat()
                self.is_visible = False
                return item
        return None

    def dismiss(self):
        self.is_visible = False

    def get_pending(self) -> list[ApprovalItem]:
        return [i for i in self.items if i.status == "pending"]

    def get_latest(self) -> Optional[ApprovalItem]:
        pending = self.get_pending()
        return pending[-1] if pending else None

    def render_modal(self) -> str:
        if not self.is_visible:
            return ""
        item = self.get_latest()
        if not item:
            return ""

        risk_colors = {"critical": "!!!", "high": "!!", "medium": "!", "low": ""}
        risk_indicator = risk_colors.get(item.risk_level, "?")

        lines = [
            f"╔══════════════════════════════════════════════════════╗",
            f"║ {self.modal_title:<52} ║",
            f"╠══════════════════════════════════════════════════════╣",
            f"║ Risk: [{risk_indicator}] {item.risk_level:<42} ║",
            f"║ {item.title[:52]:<52} ║",
            f"║ {item.description[:52]:<52} ║",
        ]

        if item.conditions:
            lines.append(f"║{'':<54}║")
            lines.append(f"║ Conditions:{'':<41}║")
            for cond in item.conditions[:3]:
                lines.append(f"║   - {cond[:48]:<48}║")

        lines.extend([
            f"║{'':<54}║",
            f"║ [A]pprove    [R]eject    [D]ismiss{'':<16}║",
            f"╚══════════════════════════════════════════════════════╝",
        ])
        return "\n".join(lines)

    def render_queue(self) -> str:
        pending = self.get_pending()
        lines = ["┌─ Approval Queue ────────────────────────────────────┐"]
        for item in pending[:5]:
            risk = {"critical": "!", "high": "H", "medium": "M", "low": "L"}.get(item.risk_level, "?")
            lines.append(f"│ [{risk}] {item.title[:35]:<35} {item.risk_level:<10} │")
        if not pending:
            lines.append(f"│ {'No pending approvals':<52} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render(self) -> str:
        if self.is_visible:
            return self.render_modal()
        return self.render_queue()

    def get_stats(self) -> dict:
        return {
            "total_items": len(self.items),
            "pending": len(self.get_pending()),
            "approved": sum(1 for i in self.items if i.status == "approved"),
            "rejected": sum(1 for i in self.items if i.status == "rejected"),
        }
