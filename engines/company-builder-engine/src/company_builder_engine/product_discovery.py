"""Product Discovery — Identify product opportunities"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class OpportunityType(Enum):
    NEW_PRODUCT = "new_product"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    INTEGRATION = "integration"
    MARKET_EXPANSION = "market_expansion"


@dataclass
class ProductOpportunity:
    id: str = field(default_factory=lambda: f"OPP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    opportunity_type: OpportunityType = OpportunityType.NEW_PRODUCT
    market_size: float = 0
    competition_level: str = ""
    technical_feasibility: float = 0
    business_viability: float = 0
    user_need_strength: float = 0
    overall_score: float = 0
    personas_addressed: list[str] = field(default_factory=list)
    pain_points_solved: list[str] = field(default_factory=list)
    key_features: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.opportunity_type.value,
            "market_size": self.market_size,
            "overall_score": self.overall_score,
            "feasibility": self.technical_feasibility,
            "viability": self.business_viability,
        }


@dataclass
class DiscoveryResult:
    id: str = field(default_factory=lambda: f"DISC-{uuid.uuid4().hex[:8]}")
    opportunities: list[ProductOpportunity] = field(default_factory=list)
    recommended_opportunity: Optional[ProductOpportunity] = None
    validation_plan: dict = field(default_factory=dict)
    next_steps: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "opportunities_count": len(self.opportunities),
            "recommended": self.recommended_opportunity.to_dict() if self.recommended_opportunity else None,
            "next_steps": self.next_steps,
        }


class ProductDiscoveryEngine:
    """Discover product opportunities from personas and market analysis."""

    def __init__(self):
        self.opportunities: dict[str, ProductOpportunity] = {}
        self.discoveries: dict[str, DiscoveryResult] = {}
        self.feature_templates: dict[str, list[str]] = {
            "productivity": ["Automation", "Templates", "Collaboration", "Analytics"],
            "analytics": ["Dashboards", "Reporting", "Predictions", "Integration"],
            "security": ["Authentication", "Encryption", "Compliance", "Monitoring"],
            "communication": ["Messaging", "Video", "File sharing", "Integration"],
            "automation": ["Workflow", "Scheduling", "Triggers", "API"],
        }

    def discover(self, personas: list[dict], market: dict) -> DiscoveryResult:
        """Discover product opportunities from personas and market data."""
        result = DiscoveryResult()
        
        # Generate opportunities based on personas and market
        opportunities = self._generate_opportunities(personas, market)
        result.opportunities = opportunities
        
        # Score and rank opportunities
        scored_opportunities = self._score_opportunities(opportunities, market)
        
        # Select recommended opportunity
        if scored_opportunities:
            result.recommended_opportunity = scored_opportunities[0]
        
        # Create validation plan
        result.validation_plan = self._create_validation_plan(scored_opportunities[:3])
        
        # Define next steps
        result.next_steps = self._define_next_steps(result.recommended_opportunity)
        
        # Store opportunities
        for opp in opportunities:
            self.opportunities[opp.id] = opp
        
        self.discoveries[result.id] = result
        return result

    def _generate_opportunities(self, personas: list[dict], market: dict) -> list[ProductOpportunity]:
        """Generate product opportunities from personas and market."""
        opportunities = []
        
        # Analyze persona pain points
        all_pain_points = []
        for persona in personas:
            all_pain_points.extend(persona.get("pain_points", []))
        
        # Generate opportunities based on pain points
        pain_point_opportunities = {
            "time-consuming": ("Automation Tool", "Automate repetitive tasks to save time", OpportunityType.FEATURE),
            "complex": ("Simplified Interface", "Create intuitive user experience", OpportunityType.IMPROVEMENT),
            "expensive": ("Cost Optimization", "Reduce operational costs through efficiency", OpportunityType.FEATURE),
            "fragmented": ("Unified Platform", "Consolidate multiple tools into one", OpportunityType.NEW_PRODUCT),
            "manual": ("Workflow Automation", "Automate manual workflows", OpportunityType.FEATURE),
            "error": ("Quality Assurance", "Implement automated quality checks", OpportunityType.FEATURE),
        }
        
        for pain_point in all_pain_points:
            for keyword, (name, desc, opp_type) in pain_point_opportunities.items():
                if keyword.lower() in pain_point.lower():
                    opp = ProductOpportunity(
                        name=name,
                        description=desc,
                        opportunity_type=opp_type,
                        pain_points_solved=[pain_point],
                    )
                    opportunities.append(opp)
        
        # Generate market-driven opportunities
        market_trends = market.get("trends", [])
        for trend in market_trends[:3]:
            opp = ProductOpportunity(
                name=f"{trend.title()} Solution",
                description=f"Leverage {trend.lower()} for competitive advantage",
                opportunity_type=OpportunityType.NEW_PRODUCT,
            )
            opportunities.append(opp)
        
        # Generate feature opportunities
        feature_categories = market.get("feature_gaps", ["productivity", "analytics"])
        for category in feature_categories[:2]:
            features = self.feature_templates.get(category, [])
            for feature in features[:2]:
                opp = ProductOpportunity(
                    name=f"{feature} Feature",
                    description=f"Add {feature.lower()} capabilities",
                    opportunity_type=OpportunityType.FEATURE,
                )
                opportunities.append(opp)
        
        return opportunities[:10]

    def _score_opportunities(self, opportunities: list[ProductOpportunity], market: dict) -> list[ProductOpportunity]:
        """Score and rank opportunities."""
        for opp in opportunities:
            # Market size score
            market_score = min(1.0, market.get("tam", 0) / 1_000_000_000)
            
            # Competition score (inverse)
            comp_level = market.get("competition_level", "medium")
            comp_scores = {"low": 0.9, "medium": 0.5, "high": 0.3}
            comp_score = comp_scores.get(comp_level, 0.5)
            
            # Technical feasibility (based on opportunity type)
            feasibility_scores = {
                OpportunityType.NEW_PRODUCT: 0.5,
                OpportunityType.FEATURE: 0.8,
                OpportunityType.IMPROVEMENT: 0.9,
                OpportunityType.INTEGRATION: 0.7,
                OpportunityType.MARKET_EXPANSION: 0.6,
            }
            feasibility = feasibility_scores.get(opp.opportunity_type, 0.5)
            
            # Business viability
            viability = 0.7 if opp.opportunity_type in [OpportunityType.FEATURE, OpportunityType.IMPROVEMENT] else 0.5
            
            # User need strength
            user_need = min(1.0, len(opp.pain_points_solved) / 3)
            
            # Calculate overall score
            overall = (market_score * 0.25 + comp_score * 0.2 + feasibility * 0.25 + 
                      viability * 0.15 + user_need * 0.15)
            
            opp.market_size = market.get("tam", 0) * 0.01
            opp.technical_feasibility = feasibility
            opp.business_viability = viability
            opp.user_need_strength = user_need
            opp.overall_score = round(overall, 2)
            opp.competition_level = comp_level
        
        # Sort by overall score
        return sorted(opportunities, key=lambda o: o.overall_score, reverse=True)

    def _create_validation_plan(self, top_opportunities: list[ProductOpportunity]) -> dict:
        """Create validation plan for top opportunities."""
        plan = {
            "phases": [
                {
                    "name": "Discovery",
                    "duration": "2 weeks",
                    "activities": ["User interviews", "Market research", "Competitive analysis"],
                },
                {
                    "name": "Validation",
                    "duration": "3 weeks",
                    "activities": ["Prototype testing", "A/B testing", "Surveys"],
                },
                {
                    "name": "Refinement",
                    "duration": "2 weeks",
                    "activities": ["Feature prioritization", "Technical feasibility", "Business case"],
                },
            ],
            "success_criteria": [
                "Positive user feedback (>80%)",
                "Market demand validation",
                "Technical feasibility confirmed",
            ],
            "resources_required": [
                "UX researcher",
                "Product manager",
                "Technical lead",
            ],
        }
        
        return plan

    def _define_next_steps(self, recommended: Optional[ProductOpportunity]) -> list[str]:
        """Define next steps based on recommended opportunity."""
        if not recommended:
            return ["Conduct more research"]
        
        steps = [
            f"Validate {recommended.name} with target users",
            "Create detailed product specification",
            "Develop technical architecture",
            "Build MVP prototype",
            "Test with beta users",
        ]
        
        return steps

    def validate_opportunity(self, opportunity_id: str, validation_data: dict) -> dict:
        """Validate an opportunity with real data."""
        opportunity = self.opportunities.get(opportunity_id)
        if not opportunity:
            return {"error": "Opportunity not found"}
        
        # Update scores based on validation
        user_feedback = validation_data.get("user_feedback", 0.5)
        market_demand = validation_data.get("market_demand", 0.5)
        technical_proof = validation_data.get("technical_proof", 0.5)
        
        new_score = (user_feedback * 0.4 + market_demand * 0.35 + technical_proof * 0.25)
        opportunity.overall_score = round(new_score, 2)
        
        # Update features based on feedback
        if "features" in validation_data:
            opportunity.key_features = validation_data["features"]
        
        return {
            "opportunity": opportunity.to_dict(),
            "validated": True,
            "new_score": new_score,
        }

    def prioritize_roadmap(self, opportunities: list[str]) -> list[dict]:
        """Prioritize opportunities for roadmap."""
        prioritized = []
        
        for opp_id in opportunities:
            opp = self.opportunities.get(opp_id)
            if opp:
                prioritized.append({
                    "id": opp.id,
                    "name": opp.name,
                    "score": opp.overall_score,
                    "effort": "Medium",  # Simplified
                    "impact": "High" if opp.overall_score > 0.7 else "Medium",
                })
        
        # Sort by score
        prioritized.sort(key=lambda x: x["score"], reverse=True)
        
        return prioritized

    def get_discovery_insights(self) -> dict:
        """Get insights from all discoveries."""
        all_opportunities = list(self.opportunities.values())
        
        if not all_opportunities:
            return {"status": "no_opportunities"}
        
        # Categorize by type
        type_counts = {}
        for opp in all_opportunities:
            opp_type = opp.opportunity_type.value
            type_counts[opp_type] = type_counts.get(opp_type, 0) + 1
        
        # Calculate average scores
        avg_score = sum(o.overall_score for o in all_opportunities) / len(all_opportunities)
        avg_feasibility = sum(o.technical_feasibility for o in all_opportunities) / len(all_opportunities)
        
        return {
            "total_opportunities": len(all_opportunities),
            "by_type": type_counts,
            "average_score": round(avg_score, 2),
            "average_feasibility": round(avg_feasibility, 2),
            "top_opportunity": all_opportunities[0].to_dict() if all_opportunities else None,
        }