"""ASTRA Command OS - Math Engine

A comprehensive mathematical research automation engine that handles conjecture generation,
theorem proving, formal verification, and mathematical exploration.
"""

from .conjecture_generator import ConjectureGenerator, Conjecture, ConjectureType
from .axiom_explorer import AxiomExplorer, AxiomSystem, Axiom
from .definition_miner import DefinitionMiner, FormalDefinition
from .theorem_search import TheoremSearch, Theorem, TheoremStatus
from .proof_planner import ProofPlanner, ProofOutline, ProofStep
from .proof_checker import ProofChecker, ProofVerification
from .lean_bridge import LeanBridge, LeanCode
from .coq_bridge import CoqBridge, CoqCode
from .isabelle_bridge import IsabelleBridge, IsabelleCode
from .symbolic_algebra import SymbolicAlgebra, AlgebraicExpression
from .category_theory_lab import CategoryTheoryLab, Category, Functor
from .topology_lab import TopologyLab, TopologicalSpace, ContinuousMap
from .number_theory_lab import NumberTheoryLab, NumberTheoreticResult
from .combinatorics_lab import CombinatoricsLab, CombinatorialStructure
from .formal_verification_queue import FormalVerificationQueue, VerificationTask
from .counterexample_finder import CounterexampleFinder, Counterexample
from .consistency_checker import ConsistencyChecker, ConsistencyResult
from .mathematical_novelty_score import MathematicalNoveltyScore, NoveltyAssessment

__all__ = [
    "ConjectureGenerator", "Conjecture", "ConjectureType",
    "AxiomExplorer", "AxiomSystem", "Axiom",
    "DefinitionMiner", "FormalDefinition",
    "TheoremSearch", "Theorem", "TheoremStatus",
    "ProofPlanner", "ProofOutline", "ProofStep",
    "ProofChecker", "ProofVerification",
    "LeanBridge", "LeanCode",
    "CoqBridge", "CoqCode",
    "IsabelleBridge", "IsabelleCode",
    "SymbolicAlgebra", "AlgebraicExpression",
    "CategoryTheoryLab", "Category", "Functor",
    "TopologyLab", "TopologicalSpace", "ContinuousMap",
    "NumberTheoryLab", "NumberTheoreticResult",
    "CombinatoricsLab", "CombinatorialStructure",
    "FormalVerificationQueue", "VerificationTask",
    "CounterexampleFinder", "Counterexample",
    "ConsistencyChecker", "ConsistencyResult",
    "MathematicalNoveltyScore", "NoveltyAssessment",
]
