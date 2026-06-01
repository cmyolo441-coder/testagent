"""Citation Validator — extract and sanity-check citations in text.

Detects:
 - URLs (and roughly verifies their shape)
 - DOIs (10.<reg>/<rest>)
 - arXiv IDs (e.g. 2401.12345 or hep-th/0001234)
 - "Author, Year" / "[1]" style references
"""
import re
from dataclasses import dataclass


URL_RE   = re.compile(r"https?://[^\s)>\]]+")
DOI_RE   = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
ARXIV_RE = re.compile(r"\barXiv:\s*(\d{4}\.\d{4,5}(v\d+)?|[a-z\-]+/\d{7}(v\d+)?)\b", re.IGNORECASE)
INLINE_RE = re.compile(r"\[(\d+)\]")
AUTHOR_YEAR_RE = re.compile(r"\b[A-Z][a-zA-Z\-]+(?:,?\s+et\s+al\.?)?\s*[\(\[]?(\d{4})[\)\]]?")


@dataclass
class CitationFinding:
    kind: str
    text: str
    location: int
    valid_shape: bool
    notes: str = ""


class CitationValidator:
    def validate(self, text: str) -> list[CitationFinding]:
        out: list[CitationFinding] = []
        for m in URL_RE.finditer(text):
            url = m.group(0).rstrip(".,);'\"")
            out.append(CitationFinding("url", url, m.start(), bool(re.match(r"https?://[\w.\-]+(/.*)?$", url)),
                                       notes="shape only — no network check"))
        for m in DOI_RE.finditer(text):
            out.append(CitationFinding("doi", m.group(0), m.start(), True))
        for m in ARXIV_RE.finditer(text):
            out.append(CitationFinding("arxiv", m.group(0), m.start(), True))
        for m in INLINE_RE.finditer(text):
            out.append(CitationFinding("inline_ref", m.group(0), m.start(), True,
                                       notes="bracketed numeric reference"))
        for m in AUTHOR_YEAR_RE.finditer(text):
            yr = int(m.group(1))
            ok = 1900 <= yr <= 2100
            out.append(CitationFinding("author_year", m.group(0), m.start(), ok,
                                       notes=f"year={yr}"))
        return out

    def summarize(self, findings: list[CitationFinding]) -> dict:
        kinds = {}
        for f in findings:
            kinds[f.kind] = kinds.get(f.kind, 0) + 1
        return {
            "total_citations": len(findings),
            "by_kind": kinds,
            "invalid": sum(1 for f in findings if not f.valid_shape),
        }
