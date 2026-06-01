"""Forensic Replay — Replay audit events for investigation and forensics"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ReplayEvent:
    original_event: dict
    replay_index: int
    original_timestamp: float
    replay_timestamp: float
    state_before: dict
    state_after: dict
    anomalies: list[str]

    def to_dict(self) -> dict:
        return {
            "replay_index": self.replay_index,
            "original_event": self.original_event,
            "original_timestamp": self.original_timestamp,
            "replay_timestamp": self.replay_timestamp,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "anomalies": self.anomalies,
        }


@dataclass
class ReplayReport:
    start_time: str
    end_time: str
    total_events: int
    events_replayed: int
    anomalies_found: int
    timeline: list[ReplayEvent]
    summary: dict
    integrity_valid: bool

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_events": self.total_events,
            "events_replayed": self.events_replayed,
            "anomalies_found": self.anomalies_found,
            "timeline": [e.to_dict() for e in self.timeline],
            "summary": self.summary,
            "integrity_valid": self.integrity_valid,
        }


class ForensicReplay:
    """Replay audit events for forensic investigation."""

    def __init__(self):
        self.replay_history: list[ReplayReport] = []

    def replay(self, events: list[dict]) -> ReplayReport:
        start = datetime.now(timezone.utc)
        timeline: list[ReplayEvent] = []
        anomalies: list[str] = []
        state: dict[str, Any] = {}

        for i, event in enumerate(events):
            state_before = dict(state)
            event_anomalies = self._analyze_event(event, state, i)

            self._apply_event(event, state)

            state_after = dict(state)

            anomalies.extend(event_anomalies)

            timeline.append(ReplayEvent(
                original_event=event,
                replay_index=i,
                original_timestamp=event.get("timestamp", 0),
                replay_timestamp=start.timestamp(),
                state_before=state_before,
                state_after=state_after,
                anomalies=event_anomalies,
            ))

        end = datetime.now(timezone.utc)

        summary = self._build_summary(events, anomalies, state)

        integrity_valid = self._verify_chain(events)

        report = ReplayReport(
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            total_events=len(events),
            events_replayed=len(timeline),
            anomalies_found=len(anomalies),
            timeline=timeline,
            summary=summary,
            integrity_valid=integrity_valid,
        )

        self.replay_history.append(report)
        return report

    def replay_subset(self, events: list[dict], event_type: str = None,
                      source: str = None, start_time: float = None,
                      end_time: float = None) -> ReplayReport:
        filtered = events

        if event_type:
            filtered = [e for e in filtered if e.get("event_type") == event_type]
        if source:
            filtered = [e for e in filtered if e.get("source") == source]
        if start_time:
            filtered = [e for e in filtered if e.get("timestamp", 0) >= start_time]
        if end_time:
            filtered = [e for e in filtered if e.get("timestamp", 0) <= end_time]

        return self.replay(filtered)

    def _analyze_event(self, event: dict, state: dict, index: int) -> list[str]:
        anomalies = []
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        timestamp = event.get("timestamp", 0)

        if timestamp <= 0:
            anomalies.append(f"Event {index}: Invalid timestamp")

        if index > 0 and timestamp < events_prev_timestamp:
            anomalies.append(f"Event {index}: Timestamp out of order")
        events_prev_timestamp = timestamp

        if event_type in ("file_deleted", "command_executed"):
            risk_score = payload.get("risk_score", 0)
            if isinstance(risk_score, (int, float)) and risk_score > 80:
                anomalies.append(f"Event {index}: High risk event ({risk_score})")

        if event_type == "approval_granted":
            risk_score = payload.get("risk_score", 0)
            if isinstance(risk_score, (int, float)) and risk_score > 70:
                anomalies.append(f"Event {index}: High risk approval granted")

        if event_type == "tool_executed" and not payload.get("success", True):
            anomalies.append(f"Event {index}: Tool execution failed")

        event_hash = event.get("event_hash", "")
        prev_hash = event.get("prev_hash", "")
        if index > 0 and prev_hash:
            expected_prev = events_prev_hash
            if prev_hash != expected_prev:
                anomalies.append(f"Event {index}: Hash chain broken")
        events_prev_hash = event_hash

        return anomalies

    def _apply_event(self, event: dict, state: dict):
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        entity_id = event.get("entity_id", "")

        if event_type not in state:
            state[event_type] = {"count": 0, "events": []}
        state[event_type]["count"] += 1
        state[event_type]["events"].append(event)

        if "tools" not in state:
            state["tools"] = {}
        tool_name = payload.get("tool_name", "")
        if tool_name:
            if tool_name not in state["tools"]:
                state["tools"][tool_name] = {"executions": 0, "successes": 0, "failures": 0}
            state["tools"][tool_name]["executions"] += 1
            if payload.get("success", True):
                state["tools"][tool_name]["successes"] += 1
            else:
                state["tools"][tool_name]["failures"] += 1

        if "approvals" not in state:
            state["approvals"] = {"approved": 0, "rejected": 0}
        if event_type == "approval_granted":
            state["approvals"]["approved"] += 1
        elif event_type == "approval_rejected":
            state["approvals"]["rejected"] += 1

    def _build_summary(self, events: list[dict], anomalies: list[str],
                       final_state: dict) -> dict:
        event_types = {}
        for e in events:
            t = e.get("event_type", "unknown")
            event_types[t] = event_types.get(t, 0) + 1

        sources = {}
        for e in events:
            s = e.get("source", "unknown")
            sources[s] = sources.get(s, 0) + 1

        timestamps = [e.get("timestamp", 0) for e in events if e.get("timestamp")]
        time_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0

        return {
            "event_type_distribution": event_types,
            "source_distribution": sources,
            "time_span_seconds": round(time_span, 2),
            "total_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / max(1, len(events)),
            "tool_stats": final_state.get("tools", {}),
            "approval_stats": final_state.get("approvals", {}),
        }

    def _verify_chain(self, events: list[dict]) -> bool:
        prev_hash = ""
        for event in events:
            stored_prev = event.get("prev_hash", "")
            if stored_prev and stored_prev != prev_hash:
                return False
            prev_hash = event.get("event_hash", "")
        return True

    def get_history(self) -> list[ReplayReport]:
        return list(self.replay_history)
