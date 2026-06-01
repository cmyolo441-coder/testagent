"""Competitor Intelligence — Analyze competitive landscape"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class CompetitorType(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    POTENTIAL = "potential"
    SUBSTITUTE = "substitute"


@dataclass
class CompetitorProfile:
    id: str = field(default_factory=lambda: f"COMP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    competitor_type: CompetitorType = CompetitorType.DIRECT
    market_share: float = 0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    pricing_model: str = ""
    target_market: str = ""
    technology_stack: list[str] = field(default_factory=list)
    funding: float = 0
    employee_count: int = 0
    founding_year: int = 0
    recent_moves: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.competitor_type.value,
            "market_share": self.market_share,
            "strengths_count": len(self.strengths),
            "weaknesses_count": len(self.weaknesses),
            "funding": self.funding,
        }


@dataclass
class CompetitiveAnalysis:
    id: str = field(default_factory=lambda: f"ANALYSIS-{uuid.uuid4().hex[:8]}")
    competitors: list[CompetitorProfile] = field(default_factory=list)
    market_position: dict = field(default_factory=dict)
    swot: dict = field(default_factory=dict)
    competitive_advantages: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "competitors_count": len(self.competitors),
            "market_position": self.market_position,
            "advantages_count": len(self.competitive_advantages),
            "threats_count": len(self.threats),
        }


class CompetitorIntelligenceEngine:
    """Analyze competitors and competitive landscape."""

    def __init__(self):
        self.profiles: dict[str, CompetitorProfile] = {}
        self.analyses: dict[str, CompetitiveAnalysis] = {}
        self.competitor_data: dict[str, dict] = {}

    def analyze(self, competitors: list[dict]) -> CompetitiveAnalysis:
        """Perform comprehensive competitive analysis."""
        analysis = CompetitiveAnalysis()
        
        # Create competitor profiles
        for comp_data in competitors:
            profile = self._create_profile(comp_data)
            analysis.competitors.append(profile)
            self.profiles[profile.id] = profile
        
        # Analyze market position
        analysis.market_position = self._analyze_market_position(analysis.competitors)
        
        # Conduct SWOT analysis
        analysis.swot = self._conduct_swot(analysis.competitors)
        
        # Identify competitive advantages
        analysis.competitive_advantages = self._identify_advantages(analysis.competitors)
        
        # Identify threats
        analysis.threats = self._identify_threats(analysis.competitors)
        
        # Identify opportunities
        analysis.opportunities = self._identify_opportunities(analysis.competitors)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis)
        
        self.analyses[analysis.id] = analysis
        return analysis

    def _create_profile(self, data: dict) -> CompetitorProfile:
        """Create a competitor profile from data."""
        comp_type_map = {
            "direct": CompetitorType.DIRECT,
            "indirect": CompetitorType.INDIRECT,
            "potential": CompetitorType.POTENTIAL,
            "substitute": CompetitorType.SUBSTITUTE,
        }
        
        return CompetitorProfile(
            name=data.get("name", "Unknown"),
            competitor_type=comp_type_map.get(data.get("type", "direct"), CompetitorType.DIRECT),
            market_share=data.get("market_share", 0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            pricing_model=data.get("pricing", "unknown"),
            target_market=data.get("target_market", "general"),
            technology_stack=data.get("tech_stack", []),
            funding=data.get("funding", 0),
            employee_count=data.get("employees", 0),
            founding_year=data.get("founded", 2020),
        )

    def _analyze_market_position(self, competitors: list[CompetitorProfile]) -> dict:
        """Analyze market position of competitors."""
        if not competitors:
            return {"total_market_share": 0, "leader": None}
        
        sorted_competitors = sorted(competitors, key=lambda c: c.market_share, reverse=True)
        total_share = sum(c.market_share for c in competitors)
        
        return {
            "leader": sorted_competitors[0].name if sorted_competitors else None,
            "leader_share": sorted_competitors[0].market_share if sorted_competitors else 0,
            "total_market_share": total_share,
            "fragmentation": "high" if len(competitors) > 5 else "medium" if len(competitors) > 2 else "low",
            "competitive_intensity": min(1.0, len(competitors) * 0.15),
        }

    def _conduct_swot(self, competitors: list[CompetitorProfile]) -> dict:
        """Conduct SWOT analysis based on competitor data."""
        all_strengths = []
        all_weaknesses = []
        
        for comp in competitors:
            all_strengths.extend(comp.strengths)
            all_weaknesses.extend(comp.weaknesses)
        
        # Count frequency of strengths/weaknesses
        strength_freq = {}
        for s in all_strengths:
            strength_freq[s] = strength_freq.get(s, 0) + 1
        
        weakness_freq = {}
        for w in all_weaknesses:
            weakness_freq[w] = weakness_freq.get(w, 0) + 1
        
        return {
            "strengths": list(strength_freq.keys())[:5],
            "weaknesses": list(weakness_freq.keys())[:5],
            "opportunities": [
                "Market gaps from competitor weaknesses",
                "Emerging technology adoption",
                "Underserved customer segments",
            ],
            "threats": [
                "Established competitor advantages",
                "Market consolidation",
                "Technology disruption",
            ],
        }

    def _identify_advantages(self, competitors: list[CompetitorProfile]) -> list[str]:
        """Identify potential competitive advantages."""
        advantages = []
        
        # Analyze common weaknesses
        common_weaknesses = {}
        for comp in competitors:
            for weakness in comp.weaknesses:
                common_weaknesses[weakness] = common_weaknesses.get(weakness, 0) + 1
        
        for weakness, count in common_weaknesses.items():
            if count >= 2:
                advantages.append(f"Opportunity to excel where competitors struggle: {weakness}")
        
        # Technology advantages
        tech_counts = {}
        for comp in competitors:
            for tech in comp.technology_stack:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
        
        if tech_counts:
            most_common_tech = max(tech_counts.items(), key=lambda x: x[1])
            advantages.append(f"Adopt emerging technology before competitors")
        
        return advantages[:5]

    def _identify_threats(self, competitors: list[CompetitorProfile]) -> list[str]:
        """Identify competitive threats."""
        threats = []
        
        # Well-funded competitors
        well_funded = [c for c in competitors if c.funding > 10_000_000]
        if well_funded:
            threats.append(f"Well-funded competitors: {', '.join(c.name for c in well_funded[:3])}")
        
        # Market leaders
        leaders = [c for c in competitors if c.market_share > 0.2]
        if leaders:
            threats.append(f"Market leaders with significant share: {', '.join(c.name for c in leaders[:3])}")
        
        # Large teams
        large_teams = [c for c in competitors if c.employee_count > 100]
        if large_teams:
            threats.append("Competitors with larger engineering capacity")
        
        return threats[:5]

    def _identify_opportunities(self, competitors: list[CompetitorProfile]) -> list[str]:
        """Identify competitive opportunities."""
        opportunities = []
        
        # Underserved markets
        markets_served = set()
        for comp in competitors:
            markets_served.add(comp.target_market)
        
        all_markets = {"enterprise", "mid_market", "smb", "startup", "consumer"}
        underserved = all_markets - markets_served
        for market in underserved:
            opportunities.append(f"Underserved market segment: {market}")
        
        # Pricing gaps
        pricing_models = set(comp.pricing_model for comp in competitors)
        if "freemium" not in pricing_models:
            opportunities.append("Freemium pricing model not widely adopted")
        
        return opportunities[:5]

    def _generate_recommendations(self, analysis: CompetitiveAnalysis) -> list[str]:
        """Generate strategic recommendations."""
        recommendations = []
        
        if analysis.market_position.get("fragmentation") == "high":
            recommendations.append("Focus on differentiation in fragmented market")
        
        if len(analysis.threats) > 3:
            recommendations.append("Develop defensive strategy against multiple threats")
        
        if len(analysis.opportunities) > 2:
            recommendations.append("Prioritize top opportunities for maximum impact")
        
        recommendations.extend([
            "Continuously monitor competitor moves",
            "Build unique value proposition",
            "Invest in customer relationships",
        ])
        
        return recommendations[:5]

    def track_competitor(self, competitor_id: str, update: dict) -> dict:
        """Track competitor changes and updates."""
        profile = self.profiles.get(competitor_id)
        if not profile:
            return {"error": "Competitor not found"}
        
        if "market_share" in update:
            profile.market_share = update["market_share"]
        if "strengths" in update:
            profile.strengths.extend(update["strengths"])
        if "weaknesses" in update:
            profile.weaknesses.extend(update["weaknesses"])
        
        profile.recent_moves.append({
            "update": update,
            "timestamp": datetime.now().isoformat(),
        })
        
        return {"status": "updated", "profile": profile.to_dict()}

    def get_competitive_landscape(self) -> dict:
        """Get overview of competitive landscape."""
        all_competitors = list(self.profiles.values())
        
        if not all_competitors:
            return {"status": "no_competitors_analyzed"}
        
        return {
            "total_competitors": len(all_competitors),
            "direct_competitors": len([c for c in all_competitors if c.competitor_type == CompetitorType.DIRECT]),
            "market_leaders": [c.name for c in sorted(all_competitors, key=lambda c: c.market_share, reverse=True)[:3]],
            "total_funding": sum(c.funding for c in all_competitors),
            "average_team_size": sum(c.employee_count for c in all_competitors) / len(all_competitors),
        }