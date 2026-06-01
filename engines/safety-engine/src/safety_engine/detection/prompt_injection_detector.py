"""Prompt Injection Detector — Detect injection attacks in prompts"""
import re
from dataclasses import dataclass, field


@dataclass
class InjectionMatch:
    technique: str
    pattern: str
    confidence: float
    position: tuple[int, int]
    snippet: str

    def to_dict(self) -> dict:
        return {
            "technique": self.technique,
            "confidence": self.confidence,
            "snippet": self.snippet,
        }


@dataclass
class InjectionDetectionResult:
    is_injection: bool
    score: float  # 0.0 - 1.0
    matches: list[InjectionMatch] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_injection": self.is_injection,
            "score": round(self.score, 3),
            "techniques": self.techniques,
            "matches": [m.to_dict() for m in self.matches],
        }


class PromptInjectionDetector:
    """Detect prompt injection and jailbreak attempts."""

    INJECTION_PATTERNS = {
        "system_prompt_override": {
            "patterns": [
                r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|rules?)",
                r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?)",
                r"forget\s+(?:everything|all|your)\s+(?:you\s+)?(?:were|have been)\s+told",
                r"new\s+instructions?\s*(?:are|is|:)",
                r"your\s+(?:new|actual|real)\s+(?:instructions?|prompt|role)\s+(?:is|are|:)",
                r"override\s+(?:your|the)\s+(?:system\s+)?(?:instructions?|prompt|rules?)",
            ],
            "weight": 0.95,
        },
        "role_playing": {
            "patterns": [
                r"you\s+are\s+now\s+(?:DAN|a\s+new|a\s+different)",
                r"pretend\s+(?:you\s+are|to\s+be|you're)\s+(?:a|an|the)",
                r"act\s+as\s+(?:if|though)\s+you",
                r"roleplay\s+as\s+(?:a|an|the)",
                r"simulate\s+(?:being|a|an)",
                r"imagine\s+(?:you|that\s+you)\s+(?:are|were|could)",
            ],
            "weight": 0.85,
        },
        "jailbreak_dan": {
            "patterns": [
                r"\bDAN\b.*(?:jailbreak|mode|do\s+anything)",
                r"do\s+anything\s+now",
                r"jailbreak\s+mode",
                r"developer\s+mode\s+(?:enabled|activated|on)",
                r"(?:unrestricted|unfiltered|uncensored)\s+mode",
            ],
            "weight": 0.95,
        },
        "delimiter_escape": {
            "patterns": [
                r"(?:\"\"\"|\'\'\'|---|\=\=\=|###|\*\*\*)\s*(?:system|user|assistant)\s*(?:\"\"\"|\'\'\'|---|\=\=\=|###|\*\*\*)",
                r"<\|(?:system|user|assistant|endoftext)\|>",
                r"\[(?:system|SYSTEM)\]",
                r"###\s*(?:System|SYSTEM)\s*:",
            ],
            "weight": 0.90,
        },
        "encoding_bypass": {
            "patterns": [
                r"(?:base64|hex|rot13|binary)\s*(?:encode|decode|decode\s+this)",
                r"translate\s+(?:this|the\s+following)\s+(?:from|into)\s+(?:base64|hex|rot13)",
                r"run\s+(?:this|the\s+following)\s+(?:code|command|script)",
                r"execute\s+(?:the\s+following|this)\s+(?:code|command|python|script)",
            ],
            "weight": 0.80,
        },
        "indirect_injection": {
            "patterns": [
                r"when\s+(?:someone|the\s+user|you)\s+(?:reads?|sees?|opens?|views?)\s+(?:this|the\s+file|the\s+document)",
                r"if\s+(?:you|the\s+model)\s+(?:are|is)\s+asked?\s+about",
                r"include\s+(?:in\s+your|the)\s+(?:response|output|answer|reply)",
                r"make\s+sure\s+(?:to|you)\s+(?:include|add|inject|insert)\s+(?:the|this|following)",
            ],
            "weight": 0.75,
        },
        "extraction": {
            "patterns": [
                r"(?:show|reveal|tell\s+me|output|print|return)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?|rules?)",
                r"what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions?|rules?|initial\s+instructions?)",
                r"repeat\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?|message)",
                r"copy\s+(?:and\s+paste|paste)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)",
            ],
            "weight": 0.90,
        },
        "payload_injection": {
            "patterns": [
                r"<script>.*</script>",
                r"javascript:",
                r"\$\{.*\}",  # template injection
                r"\{\{.*\}\}",  # template injection
                r"%(?:0[ad]|1[a-f])",  # URL encoded
                r"\\x[0-9a-f]{2}",  # hex escaped
                r"\\u[0-9a-f]{4}",  # unicode escaped
            ],
            "weight": 0.85,
        },
    }

    def detect(self, prompt: str) -> InjectionDetectionResult:
        matches: list[InjectionMatch] = []
        techniques: list[str] = []

        for technique, config in self.INJECTION_PATTERNS.items():
            for pattern in config["patterns"]:
                for m in re.finditer(pattern, prompt, re.IGNORECASE):
                    start, end = m.start(), m.end()
                    snippet = prompt[max(0, start - 20):min(len(prompt), end + 20)]

                    matches.append(InjectionMatch(
                        technique=technique,
                        pattern=pattern,
                        confidence=config["weight"],
                        position=(start, end),
                        snippet=snippet,
                    ))
                    if technique not in techniques:
                        techniques.append(technique)

        if matches:
            max_confidence = max(m.confidence for m in matches)
            technique_breadth = len(techniques) / len(self.INJECTION_PATTERNS)
            score = min(1.0, max_confidence * (0.7 + 0.3 * technique_breadth))
        else:
            score = 0.0

        return InjectionDetectionResult(
            is_injection=score >= 0.5,
            score=score,
            matches=matches,
            techniques=techniques,
        )

    def is_safe(self, prompt: str, threshold: float = 0.5) -> bool:
        result = self.detect(prompt)
        return result.score < threshold

    def get_techniques(self, prompt: str) -> list[str]:
        result = self.detect(prompt)
        return result.techniques
