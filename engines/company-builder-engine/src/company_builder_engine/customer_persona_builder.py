"""Customer Persona Builder — Create detailed customer personas"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


@dataclass
class PersonaDemographics:
    age_range: str = ""
    income_range: str = ""
    education: str = ""
    location: str = ""
    occupation: str = ""
    company_size: str = ""
    industry: str = ""


@dataclass
class PersonaBehavior:
    decision_making: str = ""
    purchasing_process: str = ""
    information_sources: list[str] = field(default_factory=list)
    technology_adoption: str = ""
    budget_authority: str = ""
    buying_frequency: str = ""


@dataclass
class PersonaPainPoints:
    primary_challenges: list[str] = field(default_factory=list)
    current_solutions: list[str] = field(default_factory=list)
    unmet_needs: list[str] = field(default_factory=list)
    frustrations: list[str] = field(default_factory=list)


@dataclass
class CustomerPersona:
    id: str = field(default_factory=lambda: f"PERSONA-{uuid.uuid4().hex[:8]}")
    name: str = ""
    role: str = ""
    demographics: PersonaDemographics = field(default_factory=PersonaDemographics)
    behavior: PersonaBehavior = field(default_factory=PersonaBehavior)
    pain_points: PersonaPainPoints = field(default_factory=PersonaPainPoints)
    goals: list[str] = field(default_factory=list)
    motivations: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    preferred_channels: list[str] = field(default_factory=list)
    content_preferences: list[str] = field(default_factory=list)
    value_propositions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "demographics": {
                "age_range": self.demographics.age_range,
                "income_range": self.demographics.income_range,
                "occupation": self.demographics.occupation,
            },
            "pain_points_count": len(self.pain_points.primary_challenges),
            "goals_count": len(self.goals),
        }


class CustomerPersonaBuilder:
    """Build detailed customer personas from research data."""

    def __init__(self):
        self.personas: dict[str, CustomerPersona] = {}
        self.persona_templates: dict[str, dict] = {
            "decision_maker": {
                "goals": ["ROI optimization", "Risk mitigation", "Strategic alignment"],
                "pain_points": ["Budget constraints", "Complex evaluation process", "Stakeholder alignment"],
                "motivations": ["Business growth", "Efficiency gains", "Competitive advantage"],
            },
            "end_user": {
                "goals": ["Productivity improvement", "Ease of use", "Task completion"],
                "pain_points": ["Complex interfaces", "Time-consuming workflows", "Lack of training"],
                "motivations": ["Job performance", "Time savings", "Career advancement"],
            },
            "technical_buyer": {
                "goals": ["Technical excellence", "Integration capability", "Scalability"],
                "pain_points": ["Technical debt", "Integration challenges", "Security concerns"],
                "motivations": ["Innovation", "System reliability", "Team productivity"],
            },
            "influencer": {
                "goals": ["Team success", "Knowledge sharing", "Best practices"],
                "pain_points": ["Information overload", "Tool proliferation", "Change management"],
                "motivations": ["Recognition", "Expertise", "Impact"],
            },
        }

    def build(self, research: dict, persona_type: str = "decision_maker") -> CustomerPersona:
        """Build a customer persona from research data."""
        persona = CustomerPersona()
        
        # Set demographics from research
        persona.demographics = self._extract_demographics(research)
        
        # Set persona type and role
        persona.name = self._generate_persona_name(persona_type, persona.demographics)
        persona.role = persona_type.replace("_", " ").title()
        
        # Set behavior patterns
        persona.behavior = self._analyze_behavior(research, persona_type)
        
        # Set pain points
        persona.pain_points = self._identify_pain_points(research, persona_type)
        
        # Set goals and motivations
        template = self.persona_templates.get(persona_type, {})
        persona.goals = template.get("goals", [])
        persona.motivations = template.get("motivations", [])
        
        # Set objections
        persona.objections = self._predict_objections(persona_type)
        
        # Set preferred channels
        persona.preferred_channels = self._identify_channels(persona_type, persona.demographics)
        
        # Set content preferences
        persona.content_preferences = self._identify_content_preferences(persona_type)
        
        # Set value propositions
        persona.value_propositions = self._create_value_propositions(persona, research)
        
        self.personas[persona.id] = persona
        return persona

    def _extract_demographics(self, research: dict) -> PersonaDemographics:
        """Extract demographics from research data."""
        return PersonaDemographics(
            age_range=research.get("target_age", "25-45"),
            income_range=research.get("target_income", "$50,000-$100,000"),
            education=research.get("education", "Bachelor's degree"),
            location=research.get("location", "Urban areas"),
            occupation=research.get("occupation", "Professional"),
            company_size=research.get("company_size", "50-200 employees"),
            industry=research.get("industry", "Technology"),
        )

    def _generate_persona_name(self, persona_type: dict, demographics: PersonaDemographics) -> str:
        """Generate a memorable persona name."""
        name_templates = {
            "decision_maker": ["Executive Emma", "Director David", "VP Victoria"],
            "end_user": ["User Uma", "Operator Oscar", "Specialist Sam"],
            "technical_buyer": ["Engineer Evan", "Architect Alex", "Lead Luna"],
            "influencer": ["Influencer Iris", "Advisor Adam", "Champion Chris"],
        }
        
        names = name_templates.get(persona_type, ["User"])
        import random
        return random.choice(names)

    def _analyze_behavior(self, research: dict, persona_type: str) -> PersonaBehavior:
        """Analyze buyer behavior patterns."""
        behavior_map = {
            "decision_maker": PersonaBehavior(
                decision_making="Data-driven, committee-based",
                purchasing_process="Formal RFP process",
                information_sources=["Industry reports", "Peer recommendations", "Analyst briefings"],
                technology_adoption="Early majority",
                budget_authority="Final approval",
                buying_frequency="Quarterly/Annual",
            ),
            "end_user": PersonaBehavior(
                decision_making="Feature-focused, ease of use",
                purchasing_process="Trial-based evaluation",
                information_sources=["Online reviews", "Free trials", "Documentation"],
                technology_adoption="Late majority",
                budget_authority="Influence only",
                buying_frequency="As needed",
            ),
            "technical_buyer": PersonaBehavior(
                decision_making="Technical evaluation, proof of concept",
                purchasing_process="Technical assessment",
                information_source=["Technical documentation", "Developer communities", "Benchmarks"],
                technology_adoption="Early adopter",
                budget_authority="Technical budget",
                buying_frequency="Project-based",
            ),
            "influencer": PersonaBehavior(
                decision_making="Peer validation, best practices",
                purchasing_process="Recommendation-based",
                information_source=["Conferences", "White papers", "Case studies"],
                technology_adoption="Early majority",
                budget_authority="Influence only",
                buying_frequency="As recommended",
            ),
        }
        
        return behavior_map.get(persona_type, PersonaBehavior())

    def _identify_pain_points(self, research: dict, persona_type: str) -> PersonaPainPoints:
        """Identify pain points from research."""
        pain_points_map = {
            "decision_maker": PersonaPainPoints(
                primary_challenges=["Revenue growth pressure", "Cost optimization", "Competitive threats"],
                current_solutions=["Legacy systems", "Multiple point solutions", "Manual processes"],
                unmet_needs=["Unified platform", "Real-time insights", "Scalable solution"],
                frustrations=["Slow ROI realization", "Complex vendor management", "Integration headaches"],
            ),
            "end_user": PersonaPainPoints(
                primary_challenges=["Time-consuming tasks", "Complex workflows", "Tool fragmentation"],
                current_solutions=["Spreadsheets", "Manual processes", "Multiple tools"],
                unmet_needs=["Automation", "Simplified interface", "Mobile access"],
                frustrations=["Poor user experience", "Lack of training", "Frequent context switching"],
            ),
            "technical_buyer": PersonaPainPoints(
                primary_challenges=["Technical debt", "Integration complexity", "Security vulnerabilities"],
                current_solutions=["Custom scripts", "Legacy infrastructure", "Multiple vendors"],
                unmet_needs=["Modern architecture", "API-first design", "Comprehensive security"],
                frustrations=["Poor documentation", "Lack of support", "Vendor lock-in"],
            ),
            "influencer": PersonaPainPoints(
                primary_challenges=["Information overload", "Tool proliferation", "Change resistance"],
                current_solutions=["Best practices guides", "Training programs", "Peer networks"],
                unmet_needs=["Knowledge sharing", "Community support", "Best practice guidance"],
                frustrations=["Lack of peer validation", "Rapid technology changes", "Resource constraints"],
            ),
        }
        
        return pain_points_map.get(persona_type, PersonaPainPoints())

    def _predict_objections(self, persona_type: str) -> list[str]:
        """Predict common objections."""
        objection_map = {
            "decision_maker": [
                "What's the ROI?",
                "How does this compare to competitors?",
                "What's the implementation timeline?",
                "What's the total cost of ownership?",
            ],
            "end_user": [
                "Is this easy to learn?",
                "Will this disrupt my workflow?",
                "What training is available?",
                "Can I try before buying?",
            ],
            "technical_buyer": [
                "How does this integrate with our stack?",
                "What are the security implications?",
                "How scalable is the solution?",
                "What's the migration path?",
            ],
            "influencer": [
                "Is this best practice?",
                "What do peers think?",
                "How proven is this approach?",
                "What's the learning curve?",
            ],
        }
        
        return objection_map.get(persona_type, [])

    def _identify_channels(self, persona_type: str, demographics: PersonaDemographics) -> list[str]:
        """Identify preferred communication channels."""
        channel_map = {
            "decision_maker": ["Executive briefings", "Industry conferences", "LinkedIn", "Email"],
            "end_user": ["Product documentation", "Online tutorials", "Community forums", "In-app messaging"],
            "technical_buyer": ["Technical documentation", "GitHub", "Developer conferences", "Stack Overflow"],
            "influencer": ["Industry blogs", "Webinars", "White papers", "Peer networks"],
        }
        
        return channel_map.get(persona_type, ["Email", "Website"])

    def _identify_content_preferences(self, persona_type: str) -> list[str]:
        """Identify content preferences."""
        content_map = {
            "decision_maker": ["Executive summaries", "ROI calculators", "Case studies", "Industry reports"],
            "end_user": ["How-to guides", "Video tutorials", "Quick start guides", "FAQ sections"],
            "technical_buyer": ["Technical documentation", "Architecture diagrams", "API references", "Benchmarks"],
            "influencer": ["Best practices guides", "Industry trends", "Peer success stories", "Research papers"],
        }
        
        return content_map.get(persona_type, [])

    def _create_value_propositions(self, persona: CustomerPersona, research: dict) -> list[str]:
        """Create tailored value propositions."""
        propositions = []
        
        for pain in persona.pain_points.primary_challenges[:3]:
            propositions.append(f"Addresses: {pain}")
        
        for goal in persona.goals[:2]:
            propositions.append(f"Enables: {goal}")
        
        return propositions

    def segment_personas(self) -> dict:
        """Segment personas by type and characteristics."""
        segments = {
            "by_type": {},
            "by_size": {},
            "by_maturity": {},
        }
        
        for persona in self.personas.values():
            # By type
            ptype = persona.role.lower()
            if ptype not in segments["by_type"]:
                segments["by_type"][ptype] = []
            segments["by_type"][ptype].append(persona.id)
            
            # By company size
            size = persona.demographics.company_size
            if size not in segments["by_size"]:
                segments["by_size"][size] = []
            segments["by_size"][size].append(persona.id)
        
        return segments

    def get_persona_insights(self) -> dict:
        """Get insights across all personas."""
        if not self.personas:
            return {"status": "no_personas"}
        
        all_pain_points = []
        all_goals = []
        
        for persona in self.personas.values():
            all_pain_points.extend(persona.pain_points.primary_challenges)
            all_goals.extend(persona.goals)
        
        # Count frequency
        pain_freq = {}
        for p in all_pain_points:
            pain_freq[p] = pain_freq.get(p, 0) + 1
        
        goal_freq = {}
        for g in all_goals:
            goal_freq[g] = goal_freq.get(g, 0) + 1
        
        return {
            "total_personas": len(self.personas),
            "common_pain_points": sorted(pain_freq.items(), key=lambda x: x[1], reverse=True)[:5],
            "common_goals": sorted(goal_freq.items(), key=lambda x: x[1], reverse=True)[:5],
            "segmentation": self.segment_personas(),
        }