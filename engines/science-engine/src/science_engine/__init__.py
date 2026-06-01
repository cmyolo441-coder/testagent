"""ASTRA Command OS - Science Engine

A comprehensive scientific research automation engine that handles hypothesis generation,
literature review, theory building, experimentation, and discovery validation.
"""

from .hypothesis_generator import HypothesisGenerator, Hypothesis, HypothesisType
from .literature_reviewer import LiteratureReviewer, LiteratureReview, Source
from .theory_builder import TheoryBuilder, Theory, Evidence
from .math_formalizer import MathFormalizer, MathematicalFormalization
from .simulation_designer import SimulationDesigner, SimulationPlan, SimulationConfig
from .experiment_planner import ExperimentPlanner, ExperimentPlan, ExperimentStep
from .experiment_runner import ExperimentRunner, ExperimentResults, DataPoint
from .data_analyzer import DataAnalyzer, AnalysisResults, StatisticalTest
from .falsification_engine import FalsificationEngine, FalsificationResult, FalsificationMethod
from .replication_manager import ReplicationManager, ReplicationResults
from .peer_review_orchestrator import PeerReviewOrchestrator, PeerReview, ReviewDecision
from .symbolic_math_bridge import SymbolicMathBridge, SymbolicRepresentation
from .numerical_solver import NumericalSolver, NumericalSolution, SolverMethod
from .uncertainty_quantifier import UncertaintyQuantifier, UncertaintyMetrics, ConfidenceInterval
from .novelty_detector import NoveltyDetector, NoveltyResult, NoveltyLevel
from .contradiction_checker import ContradictionChecker, ContradictionResult, Contradiction
from .benchmark_against_known_science import BenchmarkAgainstKnown, BenchmarkResult
from .paper_writer import PaperWriter, PaperDraft, PaperSection
from .citation_manager import CitationManager, Citation, CitationStyle
from .discovery_claim_validator import DiscoveryClaimValidator, ValidationResult, ValidationLevel

__all__ = [
    "HypothesisGenerator", "Hypothesis", "HypothesisType",
    "LiteratureReviewer", "LiteratureReview", "Source",
    "TheoryBuilder", "Theory", "Evidence",
    "MathFormalizer", "MathematicalFormalization",
    "SimulationDesigner", "SimulationPlan", "SimulationConfig",
    "ExperimentPlanner", "ExperimentPlan", "ExperimentStep",
    "ExperimentRunner", "ExperimentResults", "DataPoint",
    "DataAnalyzer", "AnalysisResults", "StatisticalTest",
    "FalsificationEngine", "FalsificationResult", "FalsificationMethod",
    "ReplicationManager", "ReplicationResults",
    "PeerReviewOrchestrator", "PeerReview", "ReviewDecision",
    "SymbolicMathBridge", "SymbolicRepresentation",
    "NumericalSolver", "NumericalSolution", "SolverMethod",
    "UncertaintyQuantifier", "UncertaintyMetrics", "ConfidenceInterval",
    "NoveltyDetector", "NoveltyResult", "NoveltyLevel",
    "ContradictionChecker", "ContradictionResult", "Contradiction",
    "BenchmarkAgainstKnown", "BenchmarkResult",
    "PaperWriter", "PaperDraft", "PaperSection",
    "CitationManager", "Citation", "CitationStyle",
    "DiscoveryClaimValidator", "ValidationResult", "ValidationLevel",
]
