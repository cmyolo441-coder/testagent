"""Literature Reviewer - Conducts automated literature reviews on scientific topics."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of literature sources."""
    JOURNAL_ARTICLE = "journal_article"
    CONFERENCE_PAPER = "conference_paper"
    BOOK = "book"
    CHAPTER = "chapter"
    REVIEW = "review"
    PREPRINT = "preprint"
    PATENT = "patent"
    THESIS = "thesis"
    TECHNICAL_REPORT = "technical_report"


class RelevanceLevel(Enum):
    """Relevance levels for sources."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TANGENTIAL = "tangential"


@dataclass
class Source:
    """Represents a literature source."""
    id: str
    title: str
    authors: List[str]
    year: int
    source_type: SourceType
    abstract: str
    key_findings: List[str]
    methodology: str
    relevance: RelevanceLevel
    relevance_score: float
    citations_count: int
    doi: Optional[str] = None
    journal: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "source_type": self.source_type.value,
            "abstract": self.abstract,
            "key_findings": self.key_findings,
            "methodology": self.methodology,
            "relevance": self.relevance.value,
            "relevance_score": self.relevance_score,
            "citations_count": self.citations_count,
            "doi": self.doi,
            "journal": self.journal,
        }


@dataclass
class LiteratureReview:
    """Results of a literature review."""
    topic: str
    query: str
    sources: List[Source]
    key_themes: List[str]
    methodology_summary: str
    findings_summary: str
    research_gaps: List[str]
    contradictions: List[str]
    consensus_points: List[str]
    timeline_summary: str
    total_sources_reviewed: int
    high_relevance_count: int
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "query": self.query,
            "sources": [s.to_dict() for s in self.sources],
            "key_themes": self.key_themes,
            "methodology_summary": self.methodology_summary,
            "findings_summary": self.findings_summary,
            "research_gaps": self.research_gaps,
            "contradictions": self.contradictions,
            "consensus_points": self.consensus_points,
            "timeline_summary": self.timeline_summary,
            "total_sources_reviewed": self.total_sources_reviewed,
            "high_relevance_count": self.high_relevance_count,
            "generated_at": self.generated_at.isoformat(),
        }


class LiteratureReviewer:
    """Conducts automated literature reviews on scientific topics.
    
    Synthesizes information from multiple sources to provide comprehensive
    overviews of research areas, identify gaps, and highlight contradictions.
    """
    
    def __init__(self):
        self._source_database: Dict[str, Source] = {}
        self._review_cache: Dict[str, LiteratureReview] = {}
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize with sample knowledge for demonstration."""
        sample_sources = [
            Source(
                id="SRC-001",
                title="Foundations of Quantum Mechanics",
                authors=["Dirac, P.A.M.", "von Neumann, J."],
                year=1930,
                source_type=SourceType.BOOK,
                abstract="Mathematical foundations of quantum theory",
                key_findings=["Hilbert space formulation", "Measurement theory"],
                methodology="Theoretical analysis",
                relevance=RelevanceLevel.HIGH,
                relevance_score=0.95,
                citations_count=15000,
                journal=None,
            ),
            Source(
                id="SRC-002",
                title="Statistical Learning Theory",
                authors=["Vapnik, V.N."],
                year=1998,
                source_type=SourceType.BOOK,
                abstract="Foundations of statistical learning and VC dimension",
                key_findings=["VC dimension", "Structural risk minimization"],
                methodology="Mathematical proof",
                relevance=RelevanceLevel.HIGH,
                relevance_score=0.88,
                citations_count=8500,
            ),
            Source(
                id="SRC-003",
                title="Deep Learning Review",
                authors=["LeCun, Y.", "Bengio, Y.", "Hinton, G."],
                year=2015,
                source_type=SourceType.JOURNAL_ARTICLE,
                abstract="Comprehensive review of deep learning methods",
                key_findings=["CNN architectures", "Backpropagation improvements"],
                methodology="Literature review",
                relevance=RelevanceLevel.HIGH,
                relevance_score=0.92,
                citations_count=25000,
                journal="Nature",
            ),
        ]
        
        for source in sample_sources:
            self._source_database[source.id] = source
    
    def review(self, topic: str, max_sources: int = 20, use_web: bool = False) -> LiteratureReview:
        """Conduct a literature review on a given topic.

        Args:
            topic: The research topic to review
            max_sources: Maximum number of sources to include
            use_web: If True, attempt to augment results with live ArXiv data

        Returns:
            LiteratureReview with synthesized findings
        """
        cache_key = f"{topic.lower().strip()}_{max_sources}_{use_web}"
        if cache_key in self._review_cache:
            return self._review_cache[cache_key]

        query = self._generate_search_query(topic)
        sources = self._search_sources(topic, max_sources, use_web=use_web)
        
        key_themes = self._extract_key_themes(sources, topic)
        methodology_summary = self._summarize_methodologies(sources)
        findings_summary = self._summarize_findings(sources)
        research_gaps = self._identify_research_gaps(sources, topic)
        contradictions = self._find_contradictions(sources)
        consensus_points = self._find_consensus(sources)
        timeline_summary = self._create_timeline_summary(sources)
        
        review = LiteratureReview(
            topic=topic,
            query=query,
            sources=sources,
            key_themes=key_themes,
            methodology_summary=methodology_summary,
            findings_summary=findings_summary,
            research_gaps=research_gaps,
            contradictions=contradictions,
            consensus_points=consensus_points,
            timeline_summary=timeline_summary,
            total_sources_reviewed=len(sources),
            high_relevance_count=sum(
                1 for s in sources if s.relevance == RelevanceLevel.HIGH
            ),
        )
        
        self._review_cache[cache_key] = review
        return review
    
    def _generate_search_query(self, topic: str) -> str:
        """Generate optimized search query from topic."""
        # Remove common stop words
        stop_words = {"the", "a", "an", "in", "on", "of", "for", "to", "and", "or", "is", "are"}
        words = topic.lower().split()
        keywords = [w for w in words if w not in stop_words]
        
        # Add synonyms/related terms
        expanded_terms = []
        for word in keywords:
            expanded_terms.append(word)
            if word in self._get_synonyms():
                expanded_terms.extend(self._get_synonyms()[word][:2])
        
        return " OR ".join(expanded_terms)
    
    def _get_synonyms(self) -> Dict[str, List[str]]:
        """Get synonyms for common scientific terms."""
        return {
            "machine": ["automated", "computational", "intelligent"],
            "learning": ["training", "optimization", "adaptation"],
            "neural": ["connectionist", "brain-inspired", "neural network"],
            "quantum": ["subatomic", "quantum mechanical", "quantum field"],
            "statistical": ["probabilistic", "stochastic", "data-driven"],
        }
    
    def _search_sources(self, topic: str, max_sources: int, use_web: bool = False) -> List[Source]:
        """Search internal knowledge base; optionally fall back to live ArXiv/Crossref via httpx when use_web=True and httpx is available."""
        topic_words = set(topic.lower().split())
        scored_sources = []

        for source in self._source_database.values():
            score = self._compute_relevance_score(source, topic_words, topic)
            if score > 0.3:
                source_copy = Source(
                    id=source.id,
                    title=source.title,
                    authors=source.authors,
                    year=source.year,
                    source_type=source.source_type,
                    abstract=source.abstract,
                    key_findings=source.key_findings,
                    methodology=source.methodology,
                    relevance=self._score_to_relevance(score),
                    relevance_score=score,
                    citations_count=source.citations_count,
                    doi=source.doi,
                    journal=source.journal,
                )
                scored_sources.append(source_copy)

        scored_sources.sort(key=lambda s: s.relevance_score, reverse=True)

        if use_web:
            try:
                web_sources = self._fetch_arxiv_sources(topic, max_sources)
                if web_sources:
                    # Combine, dedupe by id, prefer higher relevance_score
                    combined: Dict[str, Source] = {s.id: s for s in scored_sources}
                    for ws in web_sources:
                        if ws.id not in combined or ws.relevance_score > combined[ws.id].relevance_score:
                            combined[ws.id] = ws
                    merged = list(combined.values())
                    merged.sort(key=lambda s: s.relevance_score, reverse=True)
                    return merged[:max_sources]
            except Exception as exc:
                logger.warning("Web fallback failed for topic %r: %s; using KB results.", topic, exc)

        return scored_sources[:max_sources]

    def _fetch_arxiv_sources(self, topic: str, max_sources: int) -> List[Source]:
        """Fetch sources from ArXiv API via httpx; returns [] on failure."""
        try:
            import httpx  # type: ignore
        except ImportError:
            logger.warning("httpx not installed; skipping web fallback for topic %r.", topic)
            return []

        import xml.etree.ElementTree as ET
        from urllib.parse import quote_plus

        url = (
            f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(topic)}"
            f"&max_results={max_sources}"
        )

        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            xml_text = response.text
        except Exception as exc:
            logger.warning("ArXiv request failed for %r: %s", topic, exc)
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results: List[Source] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("ArXiv XML parse failed for %r: %s", topic, exc)
            return []

        topic_words = set(topic.lower().split())
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            id_el = entry.find("atom:id", ns)

            title = (title_el.text or "").strip() if title_el is not None else ""
            abstract = (summary_el.text or "").strip() if summary_el is not None else ""
            authors = [
                (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
                for a in entry.findall("atom:author", ns)
            ]
            year = 0
            if published_el is not None and published_el.text:
                try:
                    year = int(published_el.text[:4])
                except ValueError:
                    year = 0

            raw_id = (id_el.text or "").strip() if id_el is not None else title
            src_id = "ARXIV-" + hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:10]

            placeholder = Source(
                id=src_id,
                title=title,
                authors=authors,
                year=year,
                source_type=SourceType.PREPRINT,
                abstract=abstract,
                key_findings=[],
                methodology="preprint",
                relevance=RelevanceLevel.MEDIUM,
                relevance_score=0.0,
                citations_count=0,
                doi=None,
                journal="arXiv",
            )
            score = self._compute_relevance_score(placeholder, topic_words, topic)
            placeholder.relevance_score = score
            placeholder.relevance = self._score_to_relevance(score)
            results.append(placeholder)

        return results
    
    def _compute_relevance_score(
        self, source: Source, topic_words: set, topic: str
    ) -> float:
        """Compute relevance score for a source."""
        score = 0.0
        
        # Title relevance
        title_words = set(source.title.lower().split())
        title_overlap = len(topic_words & title_words)
        score += title_overlap * 0.15
        
        # Abstract relevance
        abstract_words = set(source.abstract.lower().split())
        abstract_overlap = len(topic_words & abstract_words)
        score += abstract_overlap * 0.1
        
        # Keyword presence in findings
        for finding in source.key_findings:
            finding_words = set(finding.lower().split())
            finding_overlap = len(topic_words & finding_words)
            score += finding_overlap * 0.05
        
        # Recency bonus (more recent sources get slight boost)
        year_bonus = max(0, (source.year - 1990) / 200)
        score += year_bonus * 0.1
        
        # Citation impact
        citation_bonus = min(source.citations_count / 10000, 0.2)
        score += citation_bonus
        
        # Topic phrase presence
        if topic.lower() in source.title.lower():
            score += 0.3
        if topic.lower() in source.abstract.lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Convert numeric score to relevance level."""
        if score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM
        elif score >= 0.3:
            return RelevanceLevel.LOW
        return RelevanceLevel.TANGENTIAL
    
    def _extract_key_themes(self, sources: List[Source], topic: str) -> List[str]:
        """Extract key themes from sources."""
        theme_counts: Dict[str, int] = {}
        
        # Common scientific themes
        theme_keywords = {
            "methodology": ["method", "approach", "algorithm", "technique"],
            "theory": ["theory", "framework", "model", "principle"],
            "empirical": ["experiment", "data", "observation", "measurement"],
            "review": ["review", "survey", "overview", "synthesis"],
            "application": ["application", "implementation", "deployment", "system"],
            "optimization": ["optimization", "improvement", "enhancement", "performance"],
        }
        
        for source in sources:
            text = f"{source.title} {source.abstract} {' '.join(source.key_findings)}".lower()
            for theme, keywords in theme_keywords.items():
                if any(kw in text for kw in keywords):
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Add topic-specific themes
        topic_words = topic.lower().split()
        for source in sources:
            for word in topic_words:
                if len(word) > 3 and word in source.abstract.lower():
                    theme_counts[word] = theme_counts.get(word, 0) + 1
        
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, _ in sorted_themes[:8]]
    
    def _summarize_methodologies(self, sources: List[Source]) -> str:
        """Summarize methodologies used across sources."""
        methodology_types: Dict[str, int] = {}
        
        for source in sources:
            method = source.methodology.lower()
            if "theoretic" in method or "mathematical" in method:
                methodology_types["theoretical analysis"] = methodology_types.get("theoretical analysis", 0) + 1
            elif "experiment" in method or "empirical" in method:
                methodology_types["experimental"] = methodology_types.get("experimental", 0) + 1
            elif "review" in method or "survey" in method:
                methodology_types["review/survey"] = methodology_types.get("review/survey", 0) + 1
            elif "simulat" in method:
                methodology_types["simulation"] = methodology_types.get("simulation", 0) + 1
            else:
                methodology_types["computational"] = methodology_types.get("computational", 0) + 1
        
        if not methodology_types:
            return "Methodologies not explicitly documented in reviewed sources."
        
        sorted_methods = sorted(methodology_types.items(), key=lambda x: x[1], reverse=True)
        summary_parts = [f"{method}: {count} sources" for method, count in sorted_methods[:5]]
        
        return f"The literature employs diverse methodologies: {'; '.join(summary_parts)}."
    
    def _summarize_findings(self, sources: List[Source]) -> str:
        """Summarize key findings across sources."""
        all_findings: List[str] = []
        
        for source in sources:
            all_findings.extend(source.key_findings[:2])
        
        # Deduplicate and summarize
        unique_findings = list(dict.fromkeys(all_findings))[:10]
        
        if not unique_findings:
            return "Key findings are distributed across the reviewed literature."
        
        return f"Major findings include: {'; '.join(unique_findings[:5])}. " + \
               f"Additional findings cover {len(unique_findings) - 5} more areas." if len(unique_findings) > 5 else ""
    
    def _identify_research_gaps(self, sources: List[Source], topic: str) -> List[str]:
        """Identify gaps in current research."""
        gaps = []
        
        # Check for methodological gaps
        methods_used = set(s.methodology.lower() for s in sources)
        if "experimental" not in methods_used:
            gaps.append("Lack of empirical validation through controlled experiments")
        if "theoretical" not in methods_used:
            gaps.append("Insufficient theoretical foundations")
        
        # Check for temporal gaps
        years = [s.year for s in sources]
        if years:
            year_range = max(years) - min(years)
            if year_range > 10:
                recent_sources = [s for s in sources if s.year >= max(years) - 3]
                if len(recent_sources) < len(sources) * 0.3:
                    gaps.append("Limited recent research in the area")
        
        # Check for application gaps
        findings_text = " ".join(f for s in sources for f in s.key_findings)
        if "application" not in findings_text.lower():
            gaps.append("Limited exploration of practical applications")
        
        # Topic-specific gaps
        if "quantum" in topic.lower() and "experimental" not in methods_used:
            gaps.append("Need for experimental validation of quantum theoretical predictions")
        
        return gaps[:5]
    
    def _find_contradictions(self, sources: List[Source]) -> List[str]:
        """Find contradictions between sources."""
        contradictions = []
        
        # Simple heuristic: compare key findings for opposing statements
        opposing_pairs = [
            ("increase", "decrease"),
            ("positive", "negative"),
            ("supports", "contradicts"),
            ("confirms", "refutes"),
        ]
        
        all_findings = [(s.title, f) for s in sources for f in s.key_findings]
        
        for i, (title1, finding1) in enumerate(all_findings):
            for title2, finding2 in all_findings[i+1:]:
                if title1 != title2:
                    finding1_lower = finding1.lower()
                    finding2_lower = finding2.lower()
                    for pos, neg in opposing_pairs:
                        if (pos in finding1_lower and neg in finding2_lower) or \
                           (neg in finding1_lower and pos in finding2_lower):
                            contradictions.append(
                                f"Divergent findings between {title1[:30]} and {title2[:30]}"
                            )
                            break
        
        return list(dict.fromkeys(contradictions))[:3]
    
    def _find_consensus(self, sources: List[Source]) -> List[str]:
        """Find consensus points across sources."""
        consensus = []
        
        # Find commonly mentioned findings
        finding_counts: Dict[str, int] = {}
        for source in sources:
            for finding in source.key_findings:
                normalized = finding.lower().strip()
                finding_counts[normalized] = finding_counts.get(normalized, 0) + 1
        
        # Consensus = findings mentioned in multiple sources
        for finding, count in finding_counts.items():
            if count >= 2:
                consensus.append(finding.title())
        
        return consensus[:5]
    
    def _create_timeline_summary(self, sources: List[Source]) -> str:
        """Create timeline summary of research."""
        if not sources:
            return "No sources available for timeline analysis."
        
        sorted_sources = sorted(sources, key=lambda s: s.year)
        earliest = sorted_sources[0]
        latest = sorted_sources[-1]
        
        # Group by decades
        decades: Dict[int, List[Source]] = {}
        for source in sorted_sources:
            decade = (source.year // 10) * 10
            if decade not in decades:
                decades[decade] = []
            decades[decade].append(source)
        
        timeline_parts = []
        for decade in sorted(decades.keys()):
            count = len(decades[decade])
            timeline_parts.append(f"{decade}s: {count} publications")
        
        return (
            f"Research spans from {earliest.year} to {latest.year}. "
            f"Key periods: {', '.join(timeline_parts)}."
        )
