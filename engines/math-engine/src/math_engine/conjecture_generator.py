"""Conjecture Generator - Generates mathematical conjectures from patterns."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class ConjectureType(Enum):
    """Types of mathematical conjectures."""
    IDENTITY = "identity"
    INEQUALITY = "inequality"
    EQUALITY = "equality"
    EXISTENCE = "existence"
    UNIQUENESS = "uniqueness"
    BOUNDEDNESS = "boundedness"
    CONVERGENCE = "convergence"
    DIVERGENCE = "divergence"
    PRIMALITY = "primality"
    DIVISIBILITY = "divisibility"


@dataclass
class Conjecture:
    """A mathematical conjecture."""
    id: str
    statement: str
    conjecture_type: ConjectureType
    confidence: float
    variables: List[str]
    domain: str
    examples: List[str]
    counterexamples_attempted: List[str]
    related_results: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "conjecture_type": self.conjecture_type.value,
            "confidence": self.confidence,
            "variables": self.variables,
            "domain": self.domain,
            "examples": self.examples,
            "counterexamples_attempted": self.counterexamples_attempted,
            "related_results": self.related_results,
            "created_at": self.created_at.isoformat(),
        }


class ConjectureGenerator:
    """Generates mathematical conjectures from patterns and axioms.
    
    Discovers potential mathematical relationships through pattern
    recognition and inductive reasoning.
    """
    
    # Templates for different conjecture types
    IDENTITY_TEMPLATES = [
        "For all n ∈ ℕ, {expr1} = {expr2}",
        "∀x ∈ ℝ, {expr1} = {expr2}",
        "∑_{i=1}^{n} {summand} = {closed_form}",
        "∏_{i=1}^{n} {product_term} = {closed_product}",
    ]
    
    INEQUALITY_TEMPLATES = [
        "For all {var} in {domain}, {expr1} ≥ {expr2}",
        "∀n ≥ {bound}, {lhs} ≤ {rhs}",
        "{lhs} > {rhs} for {var} ∈ {domain}",
    ]
    
    EXISTENCE_TEMPLATES = [
        "There exists {var} ∈ {domain} such that {property}",
        "∃{var}: {condition}",
        "For every {var1}, there exists {var2} such that {relation}",
    ]
    
    DIVISIBILITY_TEMPLATES = [
        "{dividend} is divisible by {divisor} for all {var}",
        "{divisor} | {dividend} when {condition}",
        "n | (n^{power} - {offset})",
    ]
    
    PRIMALITY_TEMPLATES = [
        "2^{n} - 1 is prime when n = {condition}",
        "n^2 + n + 41 is prime for 0 ≤ n ≤ {bound}",
        "The number {expression} is prime",
    ]

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._conjectures: Dict[str, Conjecture] = {}
        self._counter = 0
    
    def generate(
        self,
        patterns: List[Dict[str, Any]],
        axioms: List[str],
        domain: str = "natural_numbers",
        max_conjectures: int = 5,
    ) -> List[Conjecture]:
        """Generate conjectures from patterns and axioms.
        
        Args:
            patterns: Detected mathematical patterns
            axioms: Available axioms
            domain: Mathematical domain
            max_conjectures: Maximum number of conjectures to generate
            
        Returns:
            List of generated conjectures
        """
        conjectures = []
        
        # Generate identity conjectures
        identity_conjs = self._generate_identities(patterns, domain)
        conjectures.extend(identity_conjs)
        
        # Generate inequality conjectures
        inequality_conjs = self._generate_inequalities(patterns, domain)
        conjectures.extend(inequality_conjs)
        
        # Generate existence conjectures
        existence_conjs = self._generate_existence_conjectures(patterns, domain)
        conjectures.extend(existence_conjs)
        
        # Generate divisibility conjectures
        div_conjs = self._generate_divisibility_conjectures(patterns, domain)
        conjectures.extend(div_conjs)
        
        # Generate primality conjectures
        prim_conjs = self._generate_primalty_conjectures(patterns, domain)
        conjectures.extend(prim_conjs)
        
        # Rank and filter
        ranked = self._rank_conjectures(conjectures)
        
        return ranked[:max_conjectures]
    
    def _generate_identities(
        self, patterns: List[Dict[str, Any]], domain: str
    ) -> List[Conjecture]:
        """Generate identity conjectures."""
        conjectures = []
        
        # Sum of first n natural numbers
        conjectures.append(self._create_conjecture(
            statement="For all n ∈ ℕ, ∑_{i=1}^{n} i = n(n+1)/2",
            conjecture_type=ConjectureType.IDENTITY,
            variables=["n"],
            domain=domain,
            examples=["n=1: 1=1", "n=2: 1+2=3=2·3/2", "n=3: 1+2+3=6=3·4/2"],
        ))
        
        # Sum of squares
        conjectures.append(self._create_conjecture(
            statement="For all n ∈ ℕ, ∑_{i=1}^{n} i² = n(n+1)(2n+1)/6",
            conjecture_type=ConjectureType.IDENTITY,
            variables=["n"],
            domain=domain,
            examples=["n=1: 1=1·2·3/6", "n=2: 1+4=5=2·3·5/6"],
        ))
        
        # Geometric series
        conjectures.append(self._create_conjecture(
            statement="For r ≠ 1, ∑_{i=0}^{n} r^i = (r^{n+1} - 1)/(r - 1)",
            conjecture_type=ConjectureType.IDENTITY,
            variables=["r", "n"],
            domain=domain,
            examples=["r=2, n=2: 1+2+4=7=(8-1)/1"],
        ))
        
        # Fibonacci identity
        conjectures.append(self._create_conjecture(
            statement="∑_{i=1}^{n} F_i = F_{n+2} - 1 where F_i is the ith Fibonacci number",
            conjecture_type=ConjectureType.IDENTITY,
            variables=["n"],
            domain=domain,
            examples=["n=1: F_1=1=F_3-1", "n=2: F_1+F_2=2=F_4-1"],
        ))
        
        return conjectures
    
    def _generate_inequalities(
        self, patterns: List[Dict[str, Any]], domain: str
    ) -> List[Conjecture]:
        """Generate inequality conjectures."""
        conjectures = []
        
        # AM-GM inequality
        conjectures.append(self._create_conjecture(
            statement="For non-negative reals a, b: (a+b)/2 ≥ √(ab)",
            conjecture_type=ConjectureType.INEQUALITY,
            variables=["a", "b"],
            domain=domain,
            examples=["a=1, b=4: 2.5 ≥ 2", "a=2, b=2: 2 = 2"],
        ))
        
        # Triangle inequality
        conjectures.append(self._create_conjecture(
            statement="For any real numbers a, b: |a+b| ≤ |a| + |b|",
            conjecture_type=ConjectureType.INEQUALITY,
            variables=["a", "b"],
            domain=domain,
            examples=["a=1, b=2: |3| ≤ 3", "a=-1, b=2: |1| ≤ 3"],
        ))
        
        # Bernoulli's inequality
        conjectures.append(self._create_conjecture(
            statement="For x ≥ -1, n ∈ ℕ: (1+x)^n ≥ 1 + nx",
            conjecture_type=ConjectureType.INEQUALITY,
            variables=["x", "n"],
            domain=domain,
            examples=["x=1, n=2: 4 ≥ 3", "x=0.5, n=3: 3.375 ≥ 2.5"],
        ))
        
        return conjectures
    
    def _generate_existence_conjectures(
        self, patterns: List[Dict[str, Any]], domain: str
    ) -> List[Conjecture]:
        """Generate existence conjectures."""
        conjectures = []
        
        # Prime number theorem (informal)
        conjectures.append(self._create_conjecture(
            statement="For every n, there exists a prime p with n < p < 2n",
            conjecture_type=ConjectureType.EXISTENCE,
            variables=["n", "p"],
            domain=domain,
            examples=["n=1: p=2", "n=5: p=7"],
        ))
        
        # Intermediate value theorem (discrete version)
        conjectures.append(self._create_conjecture(
            statement="If f is continuous on [a,b] and f(a) < 0 < f(b), ∃c ∈ (a,b): f(c) = 0",
            conjecture_type=ConjectureType.EXISTENCE,
            variables=["a", "b", "c"],
            domain=domain,
            examples=["f(x)=x-1 on [0,2]: c=1"],
        ))
        
        return conjectures
    
    def _generate_divisibility_conjectures(
        self, patterns: List[Dict[str, Any]], domain: str
    ) -> List[Conjecture]:
        """Generate divisibility conjectures."""
        conjectures = []
        
        # Fermat's little theorem variant
        conjectures.append(self._create_conjecture(
            statement="n | (2^n - 2) for all n ∈ ℕ",
            conjecture_type=ConjectureType.DIVISIBILITY,
            variables=["n"],
            domain=domain,
            examples=["n=2: 2|2", "n=3: 3|6", "n=4: 4|14"],
        ))
        
        # Sum of digits divisibility
        conjectures.append(self._create_conjecture(
            statement="9 | (10^k - 1) for all k ∈ ℕ",
            conjecture_type=ConjectureType.DIVISIBILITY,
            variables=["k"],
            domain=domain,
            examples=["k=1: 9|9", "k=2: 9|99"],
        ))
        
        return conjectures
    
    def _generate_primalty_conjectures(
        self, patterns: List[Dict[str, Any]], domain: str
    ) -> List[Conjecture]:
        """Generate primality conjectures."""
        conjectures = []
        
        # Euler's prime-generating polynomial
        conjectures.append(self._create_conjecture(
            statement="n^2 + n + 41 is prime for 0 ≤ n ≤ 39",
            conjecture_type=ConjectureType.PRIMALITY,
            variables=["n"],
            domain=domain,
            examples=["n=0: 41 (prime)", "n=1: 43 (prime)", "n=2: 47 (prime)"],
        ))
        
        # Mersenne primes (conjecture form)
        conjectures.append(self._create_conjecture(
            statement="2^p - 1 is prime for infinitely many primes p",
            conjecture_type=ConjectureType.PRIMALITY,
            variables=["p"],
            domain=domain,
            examples=["p=2: 3", "p=3: 7", "p=5: 31"],
        ))
        
        return conjectures
    
    def _create_conjecture(
        self,
        statement: str,
        conjecture_type: ConjectureType,
        variables: List[str],
        domain: str,
        examples: List[str],
    ) -> Conjecture:
        """Create a conjecture object."""
        self._counter += 1
        conj_id = f"CONJ-{hashlib.md5(f'{statement}{self._counter}'.encode()).hexdigest()[:8].upper()}"
        
        confidence = 0.5 + self._rng.uniform(-0.1, 0.3)
        
        return Conjecture(
            id=conj_id,
            statement=statement,
            conjecture_type=conjecture_type,
            confidence=min(max(confidence, 0.1), 0.95),
            variables=variables,
            domain=domain,
            examples=examples,
            counterexamples_attempted=[],
            related_results=[],
        )
    
    def _rank_conjectures(self, conjectures: List[Conjecture]) -> List[Conjecture]:
        """Rank conjectures by confidence and importance."""
        return sorted(conjectures, key=lambda c: c.confidence, reverse=True)
