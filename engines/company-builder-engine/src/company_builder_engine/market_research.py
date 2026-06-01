"""Market Research — Comprehensive market analysis with TAM/SAM/SOM"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class MarketSegment(Enum):
    B2B = "b2b"
    B2C = "b2c"
    B2G = "b2g"
    B2B2C = "b2b2c"


@dataclass
class MarketAnalysis:
    id: str = field(default_factory=lambda: f"MKT-{uuid.uuid4().hex[:8]}")
    industry: str = ""
    segment: MarketSegment = MarketSegment.B2B
    tam: float = 0  # Total Addressable Market
    sam: float = 0  # Serviceable Addressable Market
    som: float = 0  # Serviceable Obtainable Market
    growth_rate: float = 0
    trends: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    customer_segments: list[dict] = field(default_factory=list)
    market_dynamics: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "industry": self.industry,
            "segment": self.segment.value,
            "tam": self.tam,
            "sam": self.sam,
            "som": self.som,
            "growth_rate": self.growth_rate,
            "trends_count": len(self.trends),
            "opportunities_count": len(self.opportunities),
        }


class MarketResearchEngine:
    """Conduct comprehensive market research with TAM/SAM/SOM analysis."""

    def __init__(self):
        self.analyses: dict[str, MarketAnalysis] = {}
        self.industry_data: dict[str, dict] = {
            "saas": {"growth_rate": 0.12, "margin": 0.7, "competition": "high"},
            "fintech": {"growth_rate": 0.15, "margin": 0.6, "competition": "high"},
            "healthtech": {"growth_rate": 0.18, "margin": 0.5, "competition": "medium"},
            "edtech": {"growth_rate": 0.14, "margin": 0.6, "competition": "medium"},
            "ecommerce": {"growth_rate": 0.10, "margin": 0.4, "competition": "very_high"},
            "ai_ml": {"growth_rate": 0.25, "margin": 0.8, "competition": "high"},
            "cybersecurity": {"growth_rate": 0.16, "margin": 0.7, "competition": "medium"},
            "cleantech": {"growth_rate": 0.20, "margin": 0.5, "competition": "medium"},
        }

    def research(self, industry: str, **kwargs) -> MarketAnalysis:
        """Conduct comprehensive market research for an industry."""
        industry_lower = industry.lower().replace(" ", "_")
        industry_info = self.industry_data.get(industry_lower, {
            "growth_rate": 0.10,
            "margin": 0.5,
            "competition": "medium"
        })
        
        analysis = MarketAnalysis(
            industry=industry,
            segment=kwargs.get("segment", MarketSegment.B2B),
        )
        
        # Calculate TAM/SAM/SOM
        base_market_size = kwargs.get("base_market_size", 10_000_000_000)
        analysis.tam = base_market_size
        analysis.sam = base_market_size * 0.3
        analysis.som = analysis.sam * 0.01
        
        # Set growth rate
        analysis.growth_rate = industry_info["growth_rate"]
        
        # Generate trends
        analysis.trends = self._identify_trends(industry_lower)
        
        # Generate challenges
        analysis.challenges = self._identify_challenges(industry_lower, industry_info["competition"])
        
        # Generate opportunities
        analysis.opportunities = self._identify_opportunities(industry_lower, analysis.trends)
        
        # Analyze customer segments
        analysis.customer_segments = self._analyze_customer_segments(industry_lower)
        
        # Analyze market dynamics
        analysis.market_dynamics = self._analyze_dynamics(industry_lower, industry_info)
        
        self.analyses[analysis.id] = analysis
        return analysis

    def _identify_trends(self, industry: str) -> list[str]:
        """Identify current market trends."""
        trend_map = {
            "saas": [
                "AI-powered automation",
                "Usage-based pricing",
                "Vertical SaaS specialization",
                "Product-led growth",
                "API-first architecture",
            ],
            "fintech": [
                "Open banking",
                "Embedded finance",
                "Cryptocurrency integration",
                "RegTech automation",
                "Neobank disruption",
            ],
            "healthtech": [
                "Telemedicine expansion",
                "AI diagnostics",
                "Wearable health tech",
                "Mental health platforms",
                "Precision medicine",
            ],
            "ai_ml": [
                "Generative AI adoption",
                "Edge AI deployment",
                "MLOps automation",
                "Explainable AI demand",
                "AI safety focus",
            ],
            "cybersecurity": [
                "Zero trust architecture",
                "AI-powered threat detection",
                "Cloud security",
                "Identity management",
                "Compliance automation",
            ],
        }
        return trend_map.get(industry, ["Digital transformation", "Data-driven decisions"])

    def _identify_challenges(self, industry: str, competition_level: str) -> list[str]:
        """Identify market challenges."""
        challenges = []
        
        if competition_level in ["high", "very_high"]:
            challenges.append("Intense competition from established players")
            challenges.append("Customer acquisition costs are high")
        
        challenges.extend([
            "Regulatory compliance requirements",
            "Technology evolution speed",
            "Talent acquisition challenges",
            "Market saturation in sub-segments",
        ])
        
        return challenges[:5]

    def _identify_opportunities(self, industry: str, trends: list[str]) -> list[str]:
        """Identify market opportunities."""
        opportunities = []
        
        for trend in trends[:3]:
            opportunities.append(f"Leverage {trend.lower()} for competitive advantage")
        
        opportunities.extend([
            "Underserved customer segments",
            "Geographic expansion potential",
            "Strategic partnership opportunities",
            "Platform/ecosystem plays",
        ])
        
        return opportunities[:5]

    def _analyze_customer_segments(self, industry: str) -> list[dict]:
        """Analyze potential customer segments."""
        segments = [
            {
                "name": "Enterprise",
                "size": "Large organizations",
                "needs": ["Scalability", "Security", "Compliance"],
                "willingness_to_pay": "high",
                "sales_cycle": "long",
            },
            {
                "name": "Mid-Market",
                "size": "Growing companies",
                "needs": ["Efficiency", "Integration", "Support"],
                "willingness_to_pay": "medium",
                "sales_cycle": "medium",
            },
            {
                "name": "SMB",
                "size": "Small businesses",
                "needs": ["Affordability", "Ease of use", "Speed"],
                "willingness_to_pay": "low",
                "sales_cycle": "short",
            },
            {
                "name": "Startup",
                "size": "Early-stage companies",
                "needs": ["Innovation", "Flexibility", "Growth potential"],
                "willingness_to_pay": "variable",
                "sales_cycle": "short",
            },
        ]
        return segments

    def _analyze_dynamics(self, industry: str, info: dict) -> dict:
        """Analyze market dynamics."""
        return {
            "competition_level": info["competition"],
            "profit_margins": info["margin"],
            "entry_barriers": "medium" if info["competition"] == "medium" else "high",
            "buyer_power": "medium",
            "supplier_power": "low",
            "substitute_threat": "medium",
            "innovation_pace": "fast" if info["growth_rate"] > 0.15 else "moderate",
        }

    def calculate_market_fit(self, analysis_id: str, product_concept: dict) -> dict:
        """Calculate product-market fit score."""
        analysis = self.analyses.get(analysis_id)
        if not analysis:
            return {"error": "Analysis not found"}
        
        score = 0
        factors = []
        
        # Market size factor
        if analysis.tam > 1_000_000_000:
            score += 0.3
            factors.append(("Market Size", 0.3))
        elif analysis.tam > 100_000_000:
            score += 0.2
            factors.append(("Market Size", 0.2))
        else:
            score += 0.1
            factors.append(("Market Size", 0.1))
        
        # Growth factor
        if analysis.growth_rate > 0.15:
            score += 0.25
            factors.append(("Growth Rate", 0.25))
        elif analysis.growth_rate > 0.10:
            score += 0.15
            factors.append(("Growth Rate", 0.15))
        else:
            score += 0.1
            factors.append(("Growth Rate", 0.1))
        
        # Competition factor
        comp_scores = {"low": 0.25, "medium": 0.15, "high": 0.1, "very_high": 0.05}
        comp_score = comp_scores.get(analysis.market_dynamics.get("competition_level", "medium"), 0.1)
        score += comp_score
        factors.append(("Competition", comp_score))
        
        return {
            "fit_score": round(score, 2),
            "factors": factors,
            "recommendation": "Strong fit" if score > 0.6 else "Moderate fit" if score > 0.4 else "Weak fit",
        }

    def get_industry_benchmarks(self, industry: str) -> dict:
        """Get industry benchmarks for comparison."""
        industry_lower = industry.lower().replace(" ", "_")
        info = self.industry_data.get(industry_lower, {"growth_rate": 0.10, "margin": 0.5})
        
        return {
            "average_growth_rate": info["growth_rate"],
            "average_margin": info["margin"],
            "typical_cac": 1000,
            "typical_ltv": 10000,
            "typical_churn_rate": 0.05,
            "typical_conversion_rate": 0.02,
        }