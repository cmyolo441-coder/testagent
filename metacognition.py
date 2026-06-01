"""MetaCognition — monitor reasoning traces and flag failure modes"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone
import hashlib
import re
import uuid


class FailureMode(Enum):
    LOOPING = "looping"
    LOW_CONFIDENCE = "low_confidence"
    CONTRADICTION = "contradiction"
    BUDGET_EXCEEDED = "budget_exceeded"
    STALLED = "stalled"
    HALLUCINATION_RISK = "hallucination_risk"
    NONE = "none"


class InterventionAction(Enum):
    PAUSE = "pause"
    REPLAN = "replan"
    ASK_USER = "ask_user"
    REDUCE_SCOPE = "reduce_scope"
    SWITCH_STRATEGY = "switch_strategy"
    ABORT = "abort"
    CONTINUE = "continue"


@dataclass
class Intervention:
    intervention_id: str
    mode: FailureMode
    action: InterventionAction
    severity: float  # 0..1
    rationale: str
    evidence_step_ids: list[int] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MetaCognition:
    """Monitor LoopStep-like dicts to detect failure modes and emit Interventions."""

    CONTRADICTION_PAIRS = [
        ("yes", "no"),
        ("true", "false"),
        ("succeed", "fail"),
        ("success", "failure"),
        ("possible", "impossible"),
        ("safe", "unsafe"),
        ("ready", "not ready"),
    ]
    HALLUCINATION_CUES = re.compile(
        r"\b(i think|i believe|probably|might be|maybe|i assume|guess|seems like)\b",
        re.IGNORECASE,
    )
    UNCERTAIN_CUES = re.compile(
        r"\b(unclear|not sure|don't know|dont know|uncertain|unknown|cannot determine)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        loop_window: int = 6,
        low_confidence_threshold: float = 0.4,
        max_budget_iterations: int = 50,
        max_budget_tokens: Optional[int] = None,
        stall_threshold: int = 3,
    ):
        self.loop_window = max(2, loop_window)
        self.low_confidence_threshold = low_confidence_threshold
        self.max_budget_iterations = max_budget_iterations
        self.max_budget_tokens = max_budget_tokens
        self.stall_threshold = stall_threshold

    def evaluate(self, steps: list[dict], budget_used: Optional[dict] = None) -> list[Intervention]:
        interventions: list[Intervention] = []
        if not steps:
            return interventions

        loop_iv = self._detect_looping(steps)
        if loop_iv:
            interventions.append(loop_iv)

        low_conf = self._detect_low_confidence(steps)
        if low_conf:
            interventions.append(low_conf)

        contradict = self._detect_contradiction(steps)
        if contradict:
            interventions.append(contradict)

        budget = self._detect_budget(steps, budget_used or {})
        if budget:
            interventions.append(budget)

        stalled = self._detect_stalled(steps)
        if stalled:
            interventions.append(stalled)

        halluc = self._detect_hallucination_risk(steps)
        if halluc:
            interventions.append(halluc)

        return interventions

    # ---- Detectors ----
    def _detect_looping(self, steps: list[dict]) -> Optional[Intervention]:
        window = steps[-self.loop_window:]
        if len(window) < 3:
            return None
        fingerprints = [self._fingerprint(s) for s in window]
        counts: dict[str, list[int]] = {}
        for idx, fp in enumerate(fingerprints):
            counts.setdefault(fp, []).append(window[idx].get("iteration", idx))
        repeated = [(fp, ids) for fp, ids in counts.items() if len(ids) >= 3]
        if not repeated:
            return None
        _, ids = max(repeated, key=lambda kv: len(kv[1]))
        severity = min(1.0, 0.4 + 0.15 * len(ids))
        return Intervention(
            intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
            mode=FailureMode.LOOPING,
            action=InterventionAction.REPLAN,
            severity=round(severity, 4),
            rationale=f"Detected {len(ids)} near-identical steps within window of {len(window)}",
            evidence_step_ids=ids,
        )

    def _detect_low_confidence(self, steps: list[dict]) -> Optional[Intervention]:
        window = steps[-self.loop_window:]
        confs: list[tuple[int, float]] = []
        for s in window:
            c = self._extract_confidence(s)
            if c is not None:
                confs.append((s.get("iteration", 0), c))
        if not confs:
            return None
        below = [(i, c) for i, c in confs if c < self.low_confidence_threshold]
        if len(below) < max(2, len(confs) // 2):
            return None
        avg = sum(c for _, c in below) / len(below)
        severity = round(min(1.0, (self.low_confidence_threshold - avg) * 2.0 + 0.3), 4)
        action = InterventionAction.ASK_USER if avg < 0.25 else InterventionAction.REPLAN
        return Intervention(
            intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
            mode=FailureMode.LOW_CONFIDENCE,
            action=action,
            severity=severity,
            rationale=f"Average confidence {avg:.2f} below threshold {self.low_confidence_threshold}",
            evidence_step_ids=[i for i, _ in below],
        )

    def _detect_contradiction(self, steps: list[dict]) -> Optional[Intervention]:
        window = steps[-self.loop_window:]
        if len(window) < 2:
            return None
        ids: list[int] = []
        for i in range(len(window)):
            for j in range(i + 1, len(window)):
                a = self._step_text(window[i]).lower()
                b = self._step_text(window[j]).lower()
                if not a or not b:
                    continue
                for x, y in self.CONTRADICTION_PAIRS:
                    if re.search(rf"\b{re.escape(x)}\b", a) and re.search(rf"\b{re.escape(y)}\b", b):
                        ids.extend([window[i].get("iteration", i), window[j].get("iteration", j)])
                    elif re.search(rf"\b{re.escape(y)}\b", a) and re.search(rf"\b{re.escape(x)}\b", b):
                        ids.extend([window[i].get("iteration", i), window[j].get("iteration", j)])
        if not ids:
            return None
        unique_ids = sorted(set(ids))
        return Intervention(
            intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
            mode=FailureMode.CONTRADICTION,
            action=InterventionAction.REPLAN,
            severity=round(min(1.0, 0.3 + 0.1 * len(unique_ids)), 4),
            rationale=f"Detected contradicting claims across {len(unique_ids)} steps",
            evidence_step_ids=unique_ids,
        )

    def _detect_budget(self, steps: list[dict], budget_used: dict) -> Optional[Intervention]:
        iters = len(steps)
        last_iter_id = steps[-1].get("iteration", iters - 1)
        if iters >= self.max_budget_iterations:
            return Intervention(
                intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
                mode=FailureMode.BUDGET_EXCEEDED,
                action=InterventionAction.ABORT,
                severity=1.0,
                rationale=f"Used {iters} iterations >= max {self.max_budget_iterations}",
                evidence_step_ids=[last_iter_id],
            )
        if self.max_budget_tokens is not None:
            used = int(budget_used.get("tokens", 0))
            if used >= self.max_budget_tokens:
                return Intervention(
                    intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
                    mode=FailureMode.BUDGET_EXCEEDED,
                    action=InterventionAction.REDUCE_SCOPE,
                    severity=1.0,
                    rationale=f"Used {used} tokens >= max {self.max_budget_tokens}",
                    evidence_step_ids=[last_iter_id],
                )
            if used >= int(self.max_budget_tokens * 0.85):
                return Intervention(
                    intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
                    mode=FailureMode.BUDGET_EXCEEDED,
                    action=InterventionAction.REDUCE_SCOPE,
                    severity=0.75,
                    rationale=f"Approaching token budget ({used}/{self.max_budget_tokens})",
                    evidence_step_ids=[last_iter_id],
                )
        return None

    def _detect_stalled(self, steps: list[dict]) -> Optional[Intervention]:
        window = steps[-self.stall_threshold:]
        if len(window) < self.stall_threshold:
            return None
        if all(not s.get("action") and not s.get("action_result") for s in window):
            ids = [s.get("iteration", i) for i, s in enumerate(window)]
            return Intervention(
                intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
                mode=FailureMode.STALLED,
                action=InterventionAction.SWITCH_STRATEGY,
                severity=0.7,
                rationale=f"No actions taken for last {self.stall_threshold} steps",
                evidence_step_ids=ids,
            )
        return None

    def _detect_hallucination_risk(self, steps: list[dict]) -> Optional[Intervention]:
        last = steps[-1]
        text = self._step_text(last)
        if not text:
            return None
        cues = len(self.HALLUCINATION_CUES.findall(text)) + len(self.UNCERTAIN_CUES.findall(text))
        if cues < 2:
            return None
        return Intervention(
            intervention_id=f"INTV-{uuid.uuid4().hex[:8]}",
            mode=FailureMode.HALLUCINATION_RISK,
            action=InterventionAction.PAUSE,
            severity=round(min(1.0, 0.3 + 0.15 * cues), 4),
            rationale=f"Multiple uncertainty/hedge cues ({cues}) in latest step",
            evidence_step_ids=[last.get("iteration", len(steps) - 1)],
        )

    # ---- Helpers ----
    def _step_text(self, step: dict) -> str:
        parts = []
        for key in ("thought", "observation", "reflection", "verification"):
            v = step.get(key)
            if isinstance(v, str) and v:
                parts.append(v)
        action = step.get("action")
        if isinstance(action, dict):
            for v in action.values():
                if isinstance(v, str):
                    parts.append(v)
        return " ".join(parts)

    def _fingerprint(self, step: dict) -> str:
        text = self._step_text(step)
        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        normalized = re.sub(r"\b\d+\b", "<N>", normalized)
        normalized = normalized[:512]
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]

    def _extract_confidence(self, step: dict) -> Optional[float]:
        for key in ("confidence", "conf", "certainty"):
            v = step.get(key)
            if isinstance(v, (int, float)):
                return max(0.0, min(1.0, float(v)))
        text = self._step_text(step)
        m = re.search(r"confidence[:=]\s*([01](?:\.\d+)?)", text, re.IGNORECASE)
        if m:
            try:
                return max(0.0, min(1.0, float(m.group(1))))
            except ValueError:
                return None
        m = re.search(r"(\d{1,3})\s*%\s*confidence", text, re.IGNORECASE)
        if m:
            try:
                return max(0.0, min(1.0, float(m.group(1)) / 100.0))
            except ValueError:
                return None
        return None

    def summary(self, interventions: list[Intervention]) -> dict:
        if not interventions:
            return {"count": 0, "modes": [], "max_severity": 0.0, "actions": []}
        modes = sorted({iv.mode.value for iv in interventions})
        actions = sorted({iv.action.value for iv in interventions})
        return {
            "count": len(interventions),
            "modes": modes,
            "actions": actions,
            "max_severity": max(iv.severity for iv in interventions),
        }
