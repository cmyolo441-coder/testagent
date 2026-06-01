"""Metacognition — Monitors agent trace for loops, low confidence, contradictions, budget."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
import uuid

from .belief_state import BeliefState


SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass
class Intervention:
    id: str = field(default_factory=lambda: f"INTV-{uuid.uuid4().hex[:8]}")
    kind: str = ""
    severity: str = "info"  # info, low, medium, high, critical
    suggestion: str = ""
    details: dict = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MetaCognition:
    """Analyses an agent trace and emits Interventions when issues are spotted."""

    def __init__(self, trace: Optional[list[dict]] = None):
        self.trace: list[dict] = list(trace or [])

    # ---------- trace management ----------

    def append(self, event: dict) -> None:
        if not isinstance(event, dict):
            raise TypeError("trace events must be dicts")
        record = dict(event)
        record.setdefault("ts", datetime.now(timezone.utc).isoformat())
        self.trace.append(record)

    def reset(self) -> None:
        self.trace.clear()

    # ---------- detectors ----------

    def detect_loop(self, window: int = 5) -> Optional[Intervention]:
        if window < 2 or len(self.trace) < window:
            return None
        recent = self.trace[-window:]
        # Compute an action signature: prefer ``action`` field, fall back to (kind, tool).
        sigs: list[str] = []
        for ev in recent:
            sig = ev.get("action") or ev.get("tool") or ev.get("kind") or ev.get("type")
            if sig is None:
                # Use a deterministic projection of the event as the signature.
                sig = "|".join(f"{k}={ev[k]}" for k in sorted(ev.keys()) if k != "ts")
            # Include arguments if present, so identical-action different-args isn't flagged.
            if "arguments" in ev:
                sig = f"{sig}::{sorted(ev['arguments'].items()) if isinstance(ev['arguments'], dict) else ev['arguments']}"
            sigs.append(str(sig))
        if len(set(sigs)) == 1:
            return Intervention(
                kind="loop_detected",
                severity="high",
                suggestion=(
                    f"The same action repeated {window} times in a row. "
                    "Try a different strategy or escalate to a human."
                ),
                details={"window": window, "action_signature": sigs[0]},
            )
        # Detect short repeating cycles (period 2 or 3).
        for period in (2, 3):
            if window >= period * 2:
                cycle = sigs[-period * 2:]
                if cycle[:period] == cycle[period:]:
                    return Intervention(
                        kind="cycle_detected",
                        severity="medium",
                        suggestion=(
                            f"A repeating cycle of length {period} was detected. "
                            "Break the cycle by varying the approach."
                        ),
                        details={"period": period, "cycle": cycle[:period]},
                    )
        return None

    def detect_low_confidence(self, threshold: float = 0.4) -> Optional[Intervention]:
        offenders: list[dict] = []
        for ev in self.trace[-20:]:
            conf = ev.get("confidence")
            if isinstance(conf, (int, float)) and conf < threshold:
                offenders.append({
                    "ts": ev.get("ts"),
                    "action": ev.get("action") or ev.get("kind"),
                    "confidence": conf,
                })
        if not offenders:
            return None
        severity = "high" if len(offenders) >= 3 else "medium"
        return Intervention(
            kind="low_confidence",
            severity=severity,
            suggestion=(
                "Recent steps had confidence below threshold. "
                "Gather more evidence, ask the user, or escalate."
            ),
            details={"threshold": threshold, "offenders": offenders},
        )

    def detect_contradiction(self, beliefs: BeliefState) -> Optional[Intervention]:
        contradictions: list[dict] = []
        # Look for trace events that assert a value that conflicts with current beliefs.
        for ev in self.trace[-50:]:
            asserted = ev.get("assert") or ev.get("assertion")
            if not isinstance(asserted, dict):
                continue
            key = asserted.get("key")
            value = asserted.get("value")
            if key is None:
                continue
            held = beliefs.get(key)
            if held is None:
                continue
            if held.value != value and held.confidence >= 0.5:
                contradictions.append({
                    "key": key,
                    "held_value": held.value,
                    "held_confidence": round(held.confidence, 3),
                    "asserted_value": value,
                    "ts": ev.get("ts"),
                })
        if not contradictions:
            return None
        return Intervention(
            kind="contradiction",
            severity="high",
            suggestion=(
                "Trace contains assertions that contradict held beliefs. "
                "Reconcile the conflict before continuing."
            ),
            details={"conflicts": contradictions},
        )

    def detect_budget_exceeded(self, used: float, limit: float) -> Optional[Intervention]:
        try:
            used = float(used)
            limit = float(limit)
        except (TypeError, ValueError):
            return None
        if limit <= 0:
            return None
        ratio = used / limit
        if ratio < 0.8:
            return None
        if ratio >= 1.0:
            severity = "critical"
            suggestion = (
                "Budget has been exceeded. Halt non-essential work and report to the user."
            )
        elif ratio >= 0.95:
            severity = "high"
            suggestion = (
                "Budget is nearly exhausted. Finish the most important task and stop."
            )
        else:
            severity = "medium"
            suggestion = (
                "Budget is above 80% utilization. Plan to wind down work soon."
            )
        return Intervention(
            kind="budget_pressure",
            severity=severity,
            suggestion=suggestion,
            details={"used": used, "limit": limit, "ratio": round(ratio, 4)},
        )

    def detect_stagnation(self, window: int = 5) -> Optional[Intervention]:
        if len(self.trace) < window:
            return None
        recent = self.trace[-window:]
        progressed = any(
            ev.get("progress") or ev.get("success") is True or ev.get("result")
            for ev in recent
        )
        if progressed:
            return None
        return Intervention(
            kind="stagnation",
            severity="medium",
            suggestion=(
                f"No measurable progress in the last {window} steps. "
                "Re-plan or ask for guidance."
            ),
            details={"window": window},
        )

    # ---------- aggregate ----------

    def evaluate(
        self,
        beliefs: Optional[BeliefState] = None,
        budget_used: Optional[float] = None,
        budget_limit: Optional[float] = None,
        loop_window: int = 5,
        confidence_threshold: float = 0.4,
    ) -> list[Intervention]:
        results: list[Intervention] = []
        loop = self.detect_loop(window=loop_window)
        if loop:
            results.append(loop)
        low_conf = self.detect_low_confidence(threshold=confidence_threshold)
        if low_conf:
            results.append(low_conf)
        if beliefs is not None:
            contra = self.detect_contradiction(beliefs)
            if contra:
                results.append(contra)
        if budget_used is not None and budget_limit is not None:
            budget = self.detect_budget_exceeded(budget_used, budget_limit)
            if budget:
                results.append(budget)
        stagnation = self.detect_stagnation(window=loop_window)
        if stagnation:
            results.append(stagnation)
        # Sort by severity descending.
        results.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 0), reverse=True)
        return results

    def summary(self, interventions: Optional[list[Intervention]] = None) -> dict:
        ivs = interventions if interventions is not None else self.evaluate()
        return {
            "trace_length": len(self.trace),
            "intervention_count": len(ivs),
            "highest_severity": ivs[0].severity if ivs else "info",
            "interventions": [
                {
                    "kind": i.kind,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "details": i.details,
                }
                for i in ivs
            ],
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
