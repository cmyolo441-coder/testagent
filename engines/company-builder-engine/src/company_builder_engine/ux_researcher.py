"""UX Researcher — Conduct user experience research"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class ResearchMethod(Enum):
    INTERVIEW = "interview"
    SURVEY = "survey"
    USABILITY_TEST = "usability_test"
    A_B_TEST = "a_b_test"
    CARD_SORTING = "card_sorting"
    TREE_TESTING = "tree_testing"
    CONTEXTUAL_INQUIRY = "contextual_inquiry"


@dataclass
class ResearchInsight:
    id: str = field(default_factory=lambda: f"INSIGHT-{uuid.uuid4().hex[:8]}")
    finding: str = ""
    evidence: str = ""
    impact: str = ""
    confidence: float = 0
    action_items: list[str] = field(default_factory=list)
    persona_relevance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "finding": self.finding,
            "impact": self.impact,
            "confidence": self.confidence,
            "action_items_count": len(self.action_items),
        }


@dataclass
class UXResearchReport:
    id: str = field(default_factory=lambda: f"UX-{uuid.uuid4().hex[:8]}")
    research_question: str = ""
    methods_used: list[ResearchMethod] = field(default_factory=list)
    participants: int = 0
    insights: list[ResearchInsight] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    personas_updated: list[str] = field(default_factory=list)
    usability_score: float = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.research_question,
            "methods": [m.value for m in self.methods_used],
            "participants": self.participants,
            "insights_count": len(self.insights),
            "usability_score": self.usability_score,
        }


class UXResearcher:
    """Conduct user experience research and generate insights."""

    def __init__(self):
        self.reports: dict[str, UXResearchReport] = {}
        self.insights: dict[str, ResearchInsight] = {}
        self.research_templates: dict[str, dict] = {
            "onboarding": {
                "methods": [ResearchMethod.USABILITY_TEST, ResearchMethod.CONTEXTUAL_INQUIRY],
                "questions": ["How intuitive is the first-time user experience?", "Where do users get stuck?"],
                "metrics": ["Time to first action", "Completion rate", "Error rate"],
            },
            "navigation": {
                "methods": [ResearchMethod.CARD_SORTING, ResearchMethod.TREE_TESTING],
                "questions": ["Can users find what they're looking for?", "Is the information architecture intuitive?"],
                "metrics": ["Find success rate", "Time on task", "Path efficiency"],
            },
            "feature_usage": {
                "methods": [ResearchMethod.A_B_TEST, ResearchMethod.SURVEY],
                "questions": ["Which features are most valuable?", "How often are features used?"],
                "metrics": ["Feature adoption rate", "Usage frequency", "User satisfaction"],
            },
            "overall_usability": {
                "methods": [ResearchMethod.USABILITY_TEST, ResearchMethod.INTERVIEW],
                "questions": ["Is the product easy to use?", "What are the pain points?"],
                "metrics": ["System Usability Scale (SUS)", "Net Promoter Score (NPS)", "Task success rate"],
            },
        }

    def research(self, personas: list[dict], research_focus: str = "overall_usability") -> UXResearchReport:
        """Conduct UX research based on personas and focus area."""
        template = self.research_templates.get(research_focus, self.research_templates["overall_usability"])
        
        report = UXResearchReport(
            research_question=template["questions"][0],
            methods_used=template["methods"],
            participants=len(personas) * 5,
        )
        
        # Generate insights based on personas
        for persona in personas:
            insights = self._generate_persona_insights(persona, research_focus)
            report.insights.extend(insights)
        
        # Calculate usability score
        report.usability_score = self._calculate_usability_score(report.insights)
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report.insights, research_focus)
        
        # Update personas
        report.personas_updated = [p.get("name", "Unknown") for p in personas]
        
        # Store insights
        for insight in report.insights:
            self.insights[insight.id] = insight
        
        self.reports[report.id] = report
        return report

    def _generate_persona_insights(self, persona: dict, research_focus: str) -> list[ResearchInsight]:
        """Generate insights for a specific persona."""
        insights = []
        persona_name = persona.get("name", "Unknown")
        
        insight_templates = {
            "onboarding": [
                ResearchInsight(
                    finding=f"{persona_name} needs simplified onboarding",
                    evidence="User struggled with initial setup",
                    impact="high",
                    confidence=0.8,
                    action_items=["Create guided tour", "Simplify form fields", "Add progress indicators"],
                    persona_relevance=[persona_name],
                ),
                ResearchInsight(
                    finding=f"{persona_name} prefers visual learning",
                    evidence="User skipped text tutorials",
                    impact="medium",
                    confidence=0.7,
                    action_items=["Add video tutorials", "Use visual cues", "Create interactive guides"],
                    persona_relevance=[persona_name],
                ),
            ],
            "navigation": [
                ResearchInsight(
                    finding=f"{persona_name} expects intuitive navigation",
                    evidence="User struggled to find key features",
                    impact="high",
                    confidence=0.85,
                    action_items=["Simplify menu structure", "Add search functionality", "Use clear labels"],
                    persona_relevance=[persona_name],
                ),
            ],
            "feature_usage": [
                ResearchInsight(
                    finding=f"{persona_name} uses core features frequently",
                    evidence="User performed main tasks multiple times",
                    impact="high",
                    confidence=0.9,
                    action_items=["Optimize core workflows", "Add shortcuts", "Improve performance"],
                    persona_relevance=[persona_name],
                ),
            ],
            "overall_usability": [
                ResearchInsight(
                    finding=f"{persona_name} values efficiency",
                    evidence="User completed tasks quickly when flow was clear",
                    impact="high",
                    confidence=0.8,
                    action_items=["Streamline workflows", "Reduce clicks", "Add keyboard shortcuts"],
                    persona_relevance=[persona_name],
                ),
                ResearchInsight(
                    finding=f"{persona_name} needs clear feedback",
                    evidence="User was uncertain if actions succeeded",
                    impact="medium",
                    confidence=0.75,
                    action_items=["Add success messages", "Show loading states", "Provide error guidance"],
                    persona_relevance=[persona_name],
                ),
            ],
        }
        
        return insight_templates.get(research_focus, insight_templates["overall_usability"])

    def _calculate_usability_score(self, insights: list[ResearchInsight]) -> float:
        """Calculate overall usability score from insights."""
        if not insights:
            return 0.5
        
        # Weight by impact and confidence
        impact_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
        
        total_score = 0
        total_weight = 0
        
        for insight in insights:
            impact_weight = impact_weights.get(insight.impact, 0.5)
            score = insight.confidence * impact_weight
            total_score += score
            total_weight += impact_weight
        
        if total_weight == 0:
            return 0.5
        
        raw_score = total_score / total_weight
        
        # Normalize to 0-100 scale
        return round(raw_score * 100, 1)

    def _generate_recommendations(self, insights: list[ResearchInsight], research_focus: str) -> list[str]:
        """Generate recommendations from insights."""
        recommendations = []
        
        # Collect all action items
        all_actions = []
        for insight in insights:
            all_actions.extend(insight.action_items)
        
        # Count frequency
        action_freq = {}
        for action in all_actions:
            action_freq[action] = action_freq.get(action, 0) + 1
        
        # Sort by frequency
        sorted_actions = sorted(action_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Add top recommendations
        for action, count in sorted_actions[:5]:
            recommendations.append(f"{action} (mentioned {count} times)")
        
        # Add research-specific recommendations
        if research_focus == "onboarding":
            recommendations.extend([
                "Create interactive product tour",
                "Simplify registration process",
                "Add contextual help",
            ])
        elif research_focus == "navigation":
            recommendations.extend([
                "Implement search functionality",
                "Simplify information architecture",
                "Add breadcrumbs for orientation",
            ])
        elif research_focus == "feature_usage":
            recommendations.extend([
                "Promote high-value features",
                "Deprecate underused features",
                "Create feature tutorials",
            ])
        else:
            recommendations.extend([
                "Conduct follow-up usability testing",
                "Implement analytics tracking",
                "Create user feedback loops",
            ])
        
        return recommendations[:8]

    def analyze_user_flows(self, flows: list[dict]) -> dict:
        """Analyze user flows for optimization opportunities."""
        analysis = {
            "total_flows": len(flows),
            "optimization_opportunities": [],
            "metrics": {},
        }
        
        for flow in flows:
            steps = flow.get("steps", [])
            completion_rate = flow.get("completion_rate", 0.5)
            drop_off_points = flow.get("drop_off_points", [])
            
            # Identify optimization opportunities
            if completion_rate < 0.7:
                analysis["optimization_opportunities"].append({
                    "flow": flow.get("name", "Unknown"),
                    "issue": "Low completion rate",
                    "suggestion": "Simplify flow or add guidance",
                })
            
            if len(steps) > 5:
                analysis["optimization_opportunities"].append({
                    "flow": flow.get("name", "Unknown"),
                    "issue": "Too many steps",
                    "suggestion": "Reduce steps or add progress indicator",
                })
            
            if drop_off_points:
                analysis["optimization_opportunities"].append({
                    "flow": flow.get("name", "Unknown"),
                    "issue": f"Drop-off at step {drop_off_points[0]}",
                    "suggestion": "Investigate and optimize drop-off point",
                })
        
        # Calculate metrics
        if flows:
            avg_completion = sum(f.get("completion_rate", 0) for f in flows) / len(flows)
            analysis["metrics"]["average_completion_rate"] = avg_completion
            analysis["metrics"]["average_steps"] = sum(len(f.get("steps", [])) for f in flows) / len(flows)
        
        return analysis

    def create_test_plan(self, research_focus: str, personas: list[dict]) -> dict:
        """Create a usability test plan."""
        template = self.research_templates.get(research_focus, self.research_templates["overall_usability"])
        
        test_plan = {
            "objective": template["questions"][0],
            "methods": [m.value for m in template["methods"]],
            "participants": [
                {
                    "persona": p.get("name", "Unknown"),
                    "count": 3,
                    "criteria": f"Matches {p.get('role', 'user')} profile",
                }
                for p in personas[:3]
            ],
            "tasks": self._generate_test_tasks(research_focus),
            "metrics": template["metrics"],
            "success_criteria": [
                "Task completion rate > 80%",
                "Average time on task < 2 minutes",
                "User satisfaction score > 4/5",
            ],
            "duration": "2 weeks",
            "resources": ["Usability testing software", "Video recording", "Note-taking templates"],
        }
        
        return test_plan

    def _generate_test_tasks(self, research_focus: str) -> list[str]:
        """Generate test tasks based on focus area."""
        task_templates = {
            "onboarding": [
                "Complete the registration process",
                "Set up your profile",
                "Complete the first key action",
            ],
            "navigation": [
                "Find the settings page",
                "Locate a specific feature",
                "Return to the dashboard",
            ],
            "feature_usage": [
                "Use the main feature to complete a task",
                "Try an advanced feature",
                "Customize your experience",
            ],
            "overall_usability": [
                "Complete your primary task",
                "Find help when needed",
                "Recover from an error",
            ],
        }
        
        return task_templates.get(research_focus, task_templates["overall_usability"])

    def get_research_insights(self) -> dict:
        """Get aggregated research insights."""
        all_insights = list(self.insights.values())
        
        if not all_insights:
            return {"status": "no_insights"}
        
        # Analyze insights
        high_impact = [i for i in all_insights if i.impact == "high"]
        low_confidence = [i for i in all_insights if i.confidence < 0.6]
        
        # Common themes
        all_action_items = []
        for insight in all_insights:
            all_action_items.extend(insight.action_items)
        
        action_freq = {}
        for action in all_action_items:
            action_freq[action] = action_freq.get(action, 0) + 1
        
        return {
            "total_insights": len(all_insights),
            "high_impact_count": len(high_impact),
            "low_confidence_count": len(low_confidence),
            "average_confidence": sum(i.confidence for i in all_insights) / len(all_insights),
            "top_actions": sorted(action_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        }