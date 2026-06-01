"""Mission Parser — Parse natural language goals into structured missions"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedMission:
    goal: str
    horizon: Optional[str] = None
    agent_count: Optional[int] = None
    verification_level: Optional[str] = None
    domain: str = "general"
    keywords: list[str] = None
    constraints: list[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.constraints is None:
            self.constraints = []


class MissionParser:
    """Parse natural language mission descriptions into structured data."""

    HORIZON_PATTERNS = [
        (r"(\d+)\s*months?", lambda m: f"{m.group(1)}m"),
        (r"(\d+)\s*weeks?", lambda m: f"{int(m.group(1))//4}m"),
        (r"(\d+)\s*years?", lambda m: f"{int(m.group(1))*12}m"),
        (r"in\s*(\d+)", lambda m: f"{m.group(1)}m"),
        (r"6\s*month", lambda _: "6m"),
        (r"1\s*year", lambda _: "12m"),
    ]

    AGENT_PATTERNS = [
        (r"(\d+)\s*agents?", lambda m: int(m.group(1))),
        (r"(\d+)\s*team", lambda m: int(m.group(1))),
        (r"with\s*(\d+)", lambda m: int(m.group(1))),
    ]

    VERIFICATION_PATTERNS = [
        (r"level[_-]?5", "level-5"),
        (r"level[_-]?4", "level-4"),
        (r"level[_-]?3", "level-3"),
        (r"level[_-]?2", "level-2"),
        (r"level[_-]?1", "level-1"),
        (r"formal", "level-5"),
        (r"adversarial", "level-4"),
        (r"independent", "level-3"),
        (r"verified", "level-3"),
    ]

    DOMAIN_KEYWORDS = {
        "company": ["company", "startup", "business", "revenue", "customer", "market"],
        "science": ["research", "experiment", "hypothesis", "paper", "discovery"],
        "math": ["proof", "theorem", "conjecture", "formula", "equation"],
        "code": ["code", "software", "app", "api", "database", "deploy"],
        "security": ["security", "audit", "vulnerability", "penetration"],
    }

    CONSTRAINT_KEYWORDS = [
        "must", "should", "cannot", "no", "without", "require", "mandatory",
    ]

    def parse(self, description: str) -> ParsedMission:
        parsed = ParsedMission(goal=description)

        # Extract horizon
        for pattern, extractor in self.HORIZON_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                parsed.horizon = extractor(match)
                break

        # Extract agent count
        for pattern, extractor in self.AGENT_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                parsed.agent_count = extractor(match)
                break

        # Extract verification level
        for pattern, level in self.VERIFICATION_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                parsed.verification_level = level
                break

        # Detect domain
        desc_lower = description.lower()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                parsed.domain = domain
                break

        # Extract keywords (words > 4 chars, not common)
        stop_words = {"the", "and", "for", "with", "this", "that", "from", "will", "have", "been", "into"}
        words = re.findall(r'\b[a-z]{5,}\b', desc_lower)
        parsed.keywords = list(set(w for w in words if w not in stop_words))[:10]

        # Extract constraints
        sentences = re.split(r'[.,;]', description)
        for sent in sentences:
            if any(kw in sent.lower() for kw in self.CONSTRAINT_KEYWORDS):
                parsed.constraints.append(sent.strip())

        return parsed
