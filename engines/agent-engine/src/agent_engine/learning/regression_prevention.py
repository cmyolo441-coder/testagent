"""Regression Prevention — Replay known-good cases and detect drift."""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass
class GoldenCase:
    id: str = field(default_factory=lambda: f"GOLD-{uuid.uuid4().hex[:8]}")
    name: str = ""
    input: Any = None
    expected_signature: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ReplayResult:
    case_id: str = ""
    name: str = ""
    passed: bool = False
    expected_signature: str = ""
    actual_signature: str = ""
    error: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RegressionPrevention:
    """Records known-good input/output signatures and replays them to detect drift."""

    def __init__(self):
        self.cases: dict[str, GoldenCase] = {}
        self.history: list[ReplayResult] = []

    @staticmethod
    def signature(output: Any) -> str:
        """Compute SHA256 over a normalized JSON representation of the output."""
        try:
            normalized = json.dumps(output, sort_keys=True, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            normalized = repr(output)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def record(
        self,
        name: str,
        input_value: Any,
        expected_output: Any,
        tags: Optional[list[str]] = None,
    ) -> GoldenCase:
        case = GoldenCase(
            name=name,
            input=input_value,
            expected_signature=self.signature(expected_output),
            tags=tags or [],
        )
        self.cases[case.id] = case
        return case

    def replay(self, runner: Callable[[Any], Any]) -> list[ReplayResult]:
        results: list[ReplayResult] = []
        for case in self.cases.values():
            result = ReplayResult(
                case_id=case.id,
                name=case.name,
                expected_signature=case.expected_signature,
            )
            try:
                actual = runner(case.input)
                result.actual_signature = self.signature(actual)
                result.passed = result.actual_signature == case.expected_signature
            except Exception as e:
                result.error = str(e)
                result.passed = False
            results.append(result)
            self.history.append(result)
        return results

    def drift(self, results: Optional[list[ReplayResult]] = None) -> list[ReplayResult]:
        source = results if results is not None else self.history
        return [r for r in source if not r.passed]

    def to_dict(self) -> dict:
        recent = self.history[-len(self.cases):] if self.cases else []
        passing = sum(1 for r in recent if r.passed)
        return {
            "cases": len(self.cases),
            "history": len(self.history),
            "last_pass_rate": (passing / len(recent)) if recent else 0.0,
        }
