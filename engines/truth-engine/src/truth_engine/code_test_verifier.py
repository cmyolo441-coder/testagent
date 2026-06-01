"""Code Test Verifier — execute project test suite, collect pass/fail, attribute
failures to specific claim IDs.
"""
import subprocess, json, re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestVerdict:
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_s: float = 0.0
    failing_tests: list[str] = field(default_factory=list)
    raw_output: str = ""

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.errors == 0 and self.total > 0


class CodeTestVerifier:
    """Runs pytest / unittest / npm test depending on what the project uses."""

    def run_pytest(self, target: str = ".", timeout: int = 300) -> TestVerdict:
        try:
            out = subprocess.run(
                ["python", "-m", "pytest", target, "-q", "--no-header"],
                capture_output=True, text=True, timeout=timeout,
            )
        except FileNotFoundError:
            return TestVerdict(raw_output="pytest unavailable")
        except subprocess.TimeoutExpired:
            return TestVerdict(raw_output="timeout")
        return self._parse_pytest(out.stdout + "\n" + out.stderr)

    @staticmethod
    def _parse_pytest(text: str) -> TestVerdict:
        v = TestVerdict(raw_output=text[-4000:])
        m = re.search(r"(\d+)\s+passed", text); v.passed = int(m.group(1)) if m else 0
        m = re.search(r"(\d+)\s+failed", text); v.failed = int(m.group(1)) if m else 0
        m = re.search(r"(\d+)\s+error",  text); v.errors = int(m.group(1)) if m else 0
        v.total = v.passed + v.failed + v.errors
        v.failing_tests = re.findall(r"FAILED (\S+)", text)
        m = re.search(r"in ([\d.]+)s", text); v.duration_s = float(m.group(1)) if m else 0.0
        return v
