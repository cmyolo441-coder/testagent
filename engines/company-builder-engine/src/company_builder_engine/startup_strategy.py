"""Startup Strategy — Develop comprehensive startup strategies"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class StrategyType(Enum):
    DISRUPTIVE = "disruptive"
    INCREMENTAL = "incremental"
    SUSTAINING = "sustaining"
    NICHE = "niche"


@dataclass
class StrategicInitiative:
    id: str = field(default_factory=lambda: f"INIT-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    priority: int = 0
    estimated_cost: float = 0
    expected_impact: float = 0
    timeline_months: int = 0
    dependencies: list[str] = field(default_factory=list)


@dataclass
class StartupStrategy:
    id: str = field(default_factory=lambda: f"STRAT-{uuid.uuid4().hex[:8]}")
    strategy_type: StrategyType = StrategyType.DISRUPTIVE
    market_research: dict = field(default_factory=dict)
    team_composition: list[dict] = field(default_factory=list)
    competitive_advantage: list[str] = field(default_factory=list)
    initiatives: list[StrategicInitiative] = field(default_factory=list)
    risk_assessment: dict = field(default_factory=dict)
    financial_projections: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.strategy_type.value,
            "advantages": self.competitive_advantage,
            "initiatives": len(self.initiatives),
            "risk_score": self.risk_assessment.get("overall_score", 0),
            "projected_revenue_y1": self.financial_projections.get("year_1_revenue", 0),
        }


class StartupStrategyEngine:
    """Develop and evaluate startup strategies based on market research and team capabilities."""

    def __init__(self):
        self.strategies: dict[str, StartupStrategy] = {}
        self.strategy_templates: dict[str, list[str]] = {
            "disruptive": ["innovation", "market_creation", "first_mover"],
            "incremental": ["improvement", "efficiency", "optimization"],
            "niche": ["specialization", "expertise", "focus"],
            "sustaining": ["reliability", "consistency", "trust"],
        }

    def develop_strategy(self, market_research: dict, team: list[dict]) -> StartupStrategy:
        """Develop a comprehensive startup strategy based on market research and team composition."""
        strategy = StartupStrategy(
            market_research=market_research,
            team_composition=team
        )

        # Analyze market to determine strategy type
        market_size = market_research.get("tam", 0)
        competition_level = market_research.get("competition_level", "medium")
        
        if competition_level == "low" and market_size > 1_000_000_000:
            strategy.strategy_type = StrategyType.DISRUPTIVE
        elif competition_level == "high":
            strategy.strategy_type = StrategyType.NICHE
        else:
            strategy.strategy_type = StrategyType.INCREMENTAL

        # Generate competitive advantages from team skills
        all_skills = []
        for member in team:
            all_skills.extend(member.get("skills", []))
        
        unique_skills = list(set(all_skills))
        strategy.competitive_advantage = self._identify_advantages(unique_skills, market_research)

        # Create strategic initiatives
        strategy.initiatives = self._create_initiatives(strategy.strategy_type, team, market_research)

        # Assess risks
        strategy.risk_assessment = self._assess_risks(strategy)

        # Generate financial projections
        strategy.financial_projections = self._project_financials(strategy, market_research)

        self.strategies[strategy.id] = strategy
        return strategy

    def _identify_advantages(self, skills: list[str], market_research: dict) -> list[str]:
        """Identify competitive advantages from team skills and market conditions."""
        advantages = []
        market_gaps = market_research.get("gaps", [])
        
        skill_advantage_map = {
            "machine_learning": "AI/ML expertise",
            "data_science": "Data-driven insights",
            "security": "Security-first approach",
            "cloud": "Scalable infrastructure",
            "devops": "Rapid deployment capability",
            "ux_design": "Superior user experience",
            "blockchain": "Decentralized solutions",
        }
        
        for skill in skills:
            if skill in skill_advantage_map:
                advantages.append(skill_advantage_map[skill])
        
        for gap in market_gaps:
            advantages.append(f"Addressing market gap: {gap}")
        
        return advantages[:5]

    def _create_initiatives(self, strategy_type: StrategyType, team: list[dict], market: dict) -> list[StrategicInitiative]:
        """Create strategic initiatives based on strategy type."""
        initiatives = []
        
        initiative_templates = {
            StrategyType.DISRUPTIVE: [
                ("MVP Development", "Build minimum viable product", 3, 50000, 0.8),
                ("Beta Testing", "Launch beta program", 2, 20000, 0.6),
                ("Market Education", "Educate market on new paradigm", 4, 30000, 0.7),
            ],
            StrategyType.NICHE: [
                ("Specialized Feature Set", "Build niche-specific features", 4, 40000, 0.7),
                ("Expert Community", "Build expert user community", 3, 15000, 0.5),
                ("Industry Partnerships", "Form strategic partnerships", 5, 25000, 0.6),
            ],
            StrategyType.INCREMENTAL: [
                ("Feature Enhancement", "Improve existing features", 2, 30000, 0.6),
                ("Performance Optimization", "Optimize system performance", 3, 20000, 0.5),
                ("User Experience Upgrade", "Enhance UI/UX", 2, 25000, 0.6),
            ],
            StrategyType.SUSTAINING: [
                ("Reliability Improvements", "Enhance system reliability", 4, 35000, 0.7),
                ("Security Hardening", "Strengthen security measures", 3, 40000, 0.8),
                ("Compliance Certification", "Obtain industry certifications", 6, 50000, 0.6),
            ],
        }
        
        templates = initiative_templates.get(strategy_type, [])
        for name, desc, timeline, cost, impact in templates:
            initiatives.append(StrategicInitiative(
                name=name,
                description=desc,
                priority=len(initiatives) + 1,
                estimated_cost=cost,
                expected_impact=impact,
                timeline_months=timeline,
            ))
        
        return initiatives

    def _assess_risks(self, strategy: StartupStrategy) -> dict:
        """Assess risks associated with the strategy."""
        risk_factors = []
        overall_risk = 0.5
        
        if strategy.strategy_type == StrategyType.DISRUPTIVE:
            risk_factors.append("Market acceptance uncertainty")
            risk_factors.append("High initial investment required")
            overall_risk = 0.7
        elif strategy.strategy_type == StrategyType.NICHE:
            risk_factors.append("Limited market size")
            risk_factors.append("Dependency on specific segment")
            overall_risk = 0.5
        else:
            risk_factors.append("Competitive pressure")
            overall_risk = 0.4
        
        team_risk = max(0, 1 - len(strategy.team_composition) / 10)
        overall_risk = (overall_risk + team_risk) / 2
        
        return {
            "factors": risk_factors,
            "overall_score": round(overall_risk, 2),
            "mitigation_strategies": self._generate_mitigations(risk_factors),
        }

    def _generate_mitigations(self, risks: list[str]) -> list[str]:
        """Generate risk mitigation strategies."""
        mitigations = []
        mitigation_map = {
            "Market acceptance": "Conduct extensive user research",
            "High initial": "Seek funding or bootstrap",
            "Limited market": "Identify adjacent markets",
            "Competitive": "Focus on unique value proposition",
            "Dependency": "Diversify revenue streams",
        }
        
        for risk in risks:
            for key, mitigation in mitigation_map.items():
                if key.lower() in risk.lower():
                    mitigations.append(mitigation)
                    break
        
        return mitigations

    def _project_financials(self, strategy: StartupStrategy, market: dict) -> dict:
        """Generate financial projections based on strategy."""
        base_cost = sum(init.estimated_cost for init in strategy.initiatives)
        team_cost = len(strategy.team_composition) * 10000
        
        return {
            "initial_investment": base_cost + team_cost,
            "monthly_burn_rate": team_cost / 6,
            "year_1_revenue": base_cost * 2,
            "break_even_months": 18,
            "projected_users_y1": 1000,
            "projected_users_y3": 10000,
            "revenue_growth_rate": 0.15,
        }

    def evaluate_strategy(self, strategy_id: str) -> dict:
        """Evaluate an existing strategy's viability."""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return {"error": "Strategy not found"}
        
        score = 0
        factors = []
        
        # Market factor
        market_score = min(1.0, strategy.market_research.get("tam", 0) / 1_000_000_000)
        score += market_score * 0.3
        factors.append(("Market Size", market_score))
        
        # Team factor
        team_score = min(1.0, len(strategy.team_composition) / 8)
        score += team_score * 0.25
        factors.append(("Team Size", team_score))
        
        # Risk factor
        risk_score = 1 - strategy.risk_assessment.get("overall_score", 0.5)
        score += risk_score * 0.25
        factors.append(("Risk Profile", risk_score))
        
        # Initiative factor
        initiative_score = min(1.0, len(strategy.initiatives) / 5)
        score += initiative_score * 0.2
        factors.append(("Initiative Coverage", initiative_score))
        
        return {
            "overall_score": round(score, 2),
            "factors": factors,
            "recommendation": "Proceed" if score > 0.6 else "Revise strategy",
        }