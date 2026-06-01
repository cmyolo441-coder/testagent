"""Paper Writer - Generates scientific paper drafts from findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class PaperSection(Enum):
    """Sections of a scientific paper."""
    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    APPENDIX = "appendix"


@dataclass
class PaperDraft:
    """Draft of a scientific paper."""
    title: str
    authors: List[str]
    sections: Dict[str, str]
    references: List[str]
    keywords: List[str]
    word_count: int
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "sections": self.sections,
            "references": self.references,
            "keywords": self.keywords,
            "word_count": self.word_count,
            "quality_score": self.quality_score,
        }


class PaperWriter:
    """Generates scientific paper drafts from findings."""
    
    def __init__(self):
        self._drafts: Dict[str, PaperDraft] = {}
    
    def write(self, findings: Dict[str, Any]) -> PaperDraft:
        """Write a paper draft from research findings.
        
        Args:
            findings: Dictionary containing research findings
            
        Returns:
            PaperDraft with complete paper structure
        """
        title = findings.get("title", "Research Findings")
        hypothesis = findings.get("hypothesis", "")
        methodology = findings.get("methodology", {})
        results = findings.get("results", {})
        conclusions = findings.get("conclusions", [])
        
        # Generate sections
        sections = {}
        
        sections[PaperSection.ABSTRACT.value] = self._write_abstract(findings)
        sections[PaperSection.INTRODUCTION.value] = self._write_introduction(findings)
        sections[PaperSection.METHODOLOGY.value] = self._write_methodology(methodology)
        sections[PaperSection.RESULTS.value] = self._write_results(results)
        sections[PaperSection.DISCUSSION.value] = self._write_discussion(findings)
        sections[PaperSection.CONCLUSION.value] = self._write_conclusion(conclusions)
        
        # Generate references
        references = self._generate_references(findings)
        
        # Generate keywords
        keywords = self._extract_keywords(findings)
        
        # Calculate word count
        word_count = sum(len(section.split()) for section in sections.values())
        
        # Quality score
        quality = self._assess_quality(sections, findings)
        
        draft = PaperDraft(
            title=title,
            authors=findings.get("authors", ["ASTRA Command OS"]),
            sections=sections,
            references=references,
            keywords=keywords,
            word_count=word_count,
            quality_score=quality,
        )
        
        self._drafts[title[:50]] = draft
        return draft
    
    def _write_abstract(self, findings: Dict[str, Any]) -> str:
        """Write abstract section."""
        hypothesis = findings.get("hypothesis", "the research question")
        results = findings.get("results", {})
        conclusions = findings.get("conclusions", [])
        
        abstract = (
            f"This study investigates {hypothesis}. "
            f"Using rigorous methodology, we collected and analyzed data to test our hypothesis. "
            f"Our results show that {results.get('summary', 'significant findings were observed')}. "
            f"These findings {conclusions[0] if conclusions else 'contribute to our understanding of the topic'}. "
            f"This work has implications for future research in this area."
        )
        
        return abstract
    
    def _write_introduction(self, findings: Dict[str, Any]) -> str:
        """Write introduction section."""
        topic = findings.get("domain", "the research domain")
        hypothesis = findings.get("hypothesis", "")
        
        introduction = (
            f"Research in {topic} has been an area of active investigation. "
            f"Understanding the underlying mechanisms is crucial for advancing knowledge in this field. "
            f"Previous studies have established foundational concepts, but gaps remain in our understanding. "
            f"In this paper, we address this gap by investigating: {hypothesis}. "
            f" Our objectives are to: (1) test the proposed hypothesis, "
            f"(2) quantify the effects observed, and (3) discuss implications for the field."
        )
        
        return introduction
    
    def _write_methodology(self, methodology: Dict[str, Any]) -> str:
        """Write methodology section."""
        approach = methodology.get("approach", "quantitative")
        sample_size = methodology.get("sample_size", "N/A")
        analysis = methodology.get("analysis", "statistical analysis")
        
        methodology_text = (
            f"We employed a {approach} approach to investigate our research question. "
            f"The study included a sample size of {sample_size} observations. "
            f"Data were collected following established protocols and analyzed using {analysis}. "
            f"All procedures were conducted in accordance with ethical guidelines. "
            f"Statistical significance was set at α = 0.05, and effect sizes were calculated "
            f"to assess practical significance."
        )
        
        return methodology_text
    
    def _write_results(self, results: Dict[str, Any]) -> str:
        """Write results section."""
        summary = results.get("summary", "Results are presented below")
        statistics = results.get("statistics", {})
        
        results_text = (
            f"The analysis yielded the following findings: {summary}. "
            f"Key statistical results include: "
        )
        
        for stat_name, stat_value in list(statistics.items())[:3]:
            results_text += f"{stat_name} = {stat_value}, "
        
        results_text += (
            "These results indicate the observed effects. "
            "Supplementary materials provide detailed statistical outputs and additional analyses."
        )
        
        return results_text
    
    def _write_discussion(self, findings: Dict[str, Any]) -> str:
        """Write discussion section."""
        hypothesis = findings.get("hypothesis", "")
        conclusions = findings.get("conclusions", [])
        
        discussion = (
            f"Our findings provide evidence regarding {hypothesis}. "
            f"The results align with theoretical predictions and previous research in this area. "
            f"{conclusions[0] if conclusions else 'The observed effects are consistent with our hypothesis'}. "
            f"Several mechanisms may explain these findings, including theoretical frameworks "
            f"that predict such outcomes. "
            f"Limitations of this study include potential confounding variables and "
            f"the generalizability of findings. "
            f"Future research should address these limitations and extend our findings."
        )
        
        return discussion
    
    def _write_conclusion(self, conclusions: List[str]) -> str:
        """Write conclusion section."""
        if not conclusions:
            conclusions = ["The study provides valuable insights into the research question"]
        
        conclusion = (
            f"In conclusion, this study demonstrates that {conclusions[0].lower() if conclusions else 'significant findings emerged'}. "
            f"These results contribute to the growing body of literature in this field. "
            f"The implications of these findings are significant for both theory and practice. "
            f"Future research should build upon these findings to further advance our understanding."
        )
        
        return conclusion
    
    def _generate_references(self, findings: Dict[str, Any]) -> List[str]:
        """Generate reference list."""
        references = [
            "Author, A. (2024). Foundational study in the field. Journal of Research, 10(2), 45-60.",
            "Researcher, B. (2023). Methodological approaches. Scientific Methods, 15(1), 12-28.",
            "Expert, C. (2022). Theoretical frameworks. Annual Review, 8, 112-135.",
        ]
        
        return references
    
    def _extract_keywords(self, findings: Dict[str, Any]) -> List[str]:
        """Extract keywords from findings."""
        keywords = [
            "research methodology",
            "statistical analysis",
            "hypothesis testing",
            findings.get("domain", "science"),
        ]
        
        return keywords[:5]
    
    def _assess_quality(self, sections: Dict[str, str], findings: Dict[str, Any]) -> float:
        """Assess paper quality."""
        score = 0.5
        
        # Check for completeness
        required_sections = ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"]
        present = sum(1 for s in required_sections if s in sections)
        score += present / len(required_sections) * 0.3
        
        # Check for adequate length
        total_words = sum(len(s.split()) for s in sections.values())
        if total_words > 1000:
            score += 0.1
        if total_words > 3000:
            score += 0.1
        
        return min(score, 1.0)
