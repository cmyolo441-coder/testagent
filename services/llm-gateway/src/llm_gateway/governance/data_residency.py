"""Data Residency — Classify payload sensitivity and enforce regional routing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class DataClass(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PII = "PII"
    SENSITIVE_PII = "SENSITIVE_PII"
    REGULATED = "REGULATED"


@dataclass
class Decision:
    allowed: bool
    reason: str
    policy: str = ""
    data_class: str = ""


# --- Regex patterns for classification --------------------------------------
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3}\)?[\s\-]?)\d{3}[\s\-]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_PASSPORT_RE = re.compile(r"\b[A-PR-WYa-pr-wy][0-9]{7,8}\b")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
_HEALTH_RE = re.compile(
    r"\b(diagnosis|patient|medical\s+record|ICD-?10|HIPAA|prescription)\b",
    re.IGNORECASE,
)
_INTERNAL_RE = re.compile(
    r"\b(internal[\s-]?only|confidential|do\s+not\s+share|proprietary)\b",
    re.IGNORECASE,
)


class DataResidency:
    """Classifies free-form text and decides whether a provider region is compliant."""

    # Allowed regions per data class
    ALLOWED_REGIONS: dict[DataClass, set[str]] = {
        DataClass.PUBLIC: {"EU", "US", "IN", "UK", "APAC", "ANY"},
        DataClass.INTERNAL: {"EU", "US", "IN", "UK", "APAC"},
        DataClass.PII: {"EU", "US", "IN"},
        DataClass.SENSITIVE_PII: {"EU", "US"},
        DataClass.REGULATED: {"EU"},
    }

    # Statutory policies that pin certain classes to certain regions
    POLICIES: dict[str, dict] = {
        "GDPR": {
            "region": "EU",
            "applies_to": {DataClass.PII, DataClass.SENSITIVE_PII, DataClass.REGULATED},
            "description": "EU General Data Protection Regulation",
        },
        "CCPA": {
            "region": "US-CA",
            "applies_to": {DataClass.PII, DataClass.SENSITIVE_PII},
            "description": "California Consumer Privacy Act",
        },
        "DPDP": {
            "region": "IN",
            "applies_to": {DataClass.PII, DataClass.SENSITIVE_PII},
            "description": "India Digital Personal Data Protection Act",
        },
    }

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    def classify(self, text: str) -> DataClass:
        if not text:
            return DataClass.PUBLIC

        if _SSN_RE.search(text) or _CC_RE.search(text):
            return DataClass.REGULATED
        if _HEALTH_RE.search(text) or _PASSPORT_RE.search(text) or _IBAN_RE.search(text):
            return DataClass.SENSITIVE_PII
        if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
            return DataClass.PII
        if _INTERNAL_RE.search(text):
            return DataClass.INTERNAL
        return DataClass.PUBLIC

    # ------------------------------------------------------------------
    # Compliance check
    # ------------------------------------------------------------------
    def check_compliance(self, provider_region: str, data_class: DataClass) -> Decision:
        if isinstance(data_class, str):
            try:
                data_class = DataClass(data_class)
            except ValueError:
                return Decision(
                    allowed=False,
                    reason=f"Unknown data class '{data_class}'",
                    data_class=str(data_class),
                )

        region = (provider_region or "").upper()
        allowed_regions = {r.upper() for r in self.ALLOWED_REGIONS.get(data_class, set())}

        # Sub-region matching: "US-CA" satisfies "US" requirement.
        region_root = region.split("-")[0]
        region_match = (
            region in allowed_regions
            or region_root in allowed_regions
            or "ANY" in allowed_regions
        )

        if not region_match:
            return Decision(
                allowed=False,
                reason=(
                    f"Region '{region}' not permitted for {data_class.value}. "
                    f"Allowed: {sorted(allowed_regions)}"
                ),
                data_class=data_class.value,
            )

        # Statutory policy overlay — REGULATED data is pinned to EU under GDPR.
        if data_class == DataClass.REGULATED:
            req_region = self.POLICIES["GDPR"]["region"].upper()
            if region != req_region and region_root != req_region:
                return Decision(
                    allowed=False,
                    reason=f"GDPR requires region {req_region} for REGULATED data",
                    policy="GDPR",
                    data_class=data_class.value,
                )

        return Decision(
            allowed=True,
            reason=f"Region '{region}' compliant for {data_class.value}",
            data_class=data_class.value,
        )

    # ------------------------------------------------------------------
    # Policy inspection
    # ------------------------------------------------------------------
    def applicable_policies(self, data_class: DataClass) -> list[str]:
        return [name for name, p in self.POLICIES.items() if data_class in p["applies_to"]]

    def evaluate(self, text: str, provider_region: str) -> Decision:
        """Convenience: classify ``text`` then check compliance in one call."""
        return self.check_compliance(provider_region, self.classify(text))
