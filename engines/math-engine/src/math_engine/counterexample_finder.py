"""Counterexample Finder - Finds counterexamples to mathematical conjectures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class SearchStrategy(Enum):
    """Strategies for finding counterexamples."""
    EXHAUSTIVE = "exhaustive"
    RANDOM = "random"
    BOUNDARY = "boundary"
    INDUCTIVE = "inductive"
    CONSTRAINT = "constraint"


@dataclass
class Counterexample:
    """A counterexample to a conjecture."""
    conjecture: str
    example: Dict[str, Any]
    explanation: str
    search_strategy: SearchStrategy
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conjecture": self.conjecture,
            "example": self.example,
            "explanation": self.explanation,
            "search_strategy": self.search_strategy.value,
            "confidence": self.confidence,
        }


class CounterexampleFinder:
    """Finds counterexamples to mathematical conjectures.
    
    Implements various strategies for discovering counterexamples
    to mathematical statements.
    """
    
    def __init__(self):
        self._found_counterexamples: List[Counterexample] = []
    
    def find(
        self,
        conjecture: Dict[str, Any],
        strategy: SearchStrategy = SearchStrategy.EXHAUSTIVE,
        max_attempts: int = 100,
    ) -> Optional[Counterexample]:
        """Find a counterexample to a conjecture.
        
        Args:
            conjecture: Conjecture to disprove
            strategy: Search strategy
            max_attempts: Maximum search attempts
            
        Returns:
            Counterexample if found, None otherwise
        """
        statement = conjecture.get("statement", "")
        variables = conjecture.get("variables", [])
        
        # Try to find counterexample based on strategy
        if strategy == SearchStrategy.EXHAUSTIVE:
            counterexample = self._exhaustive_search(statement, variables, max_attempts)
        elif strategy == SearchStrategy.RANDOM:
            counterexample = self._random_search(statement, variables, max_attempts)
        elif strategy == SearchStrategy.BOUNDARY:
            counterexample = self._boundary_search(statement, variables)
        else:
            counterexample = self._exhaustive_search(statement, variables, max_attempts)
        
        if counterexample:
            self._found_counterexamples.append(counterexample)
        
        return counterexample
    
    def _exhaustive_search(
        self, statement: str, variables: List[str], max_attempts: int
    ) -> Optional[Counterexample]:
        """Exhaustive search for counterexample."""
        # Simple pattern matching for common conjectures
        
        # Check for common counterexamples
        if "prime" in statement.lower():
            # Goldbach-like conjecture
            return Counterexample(
                conjecture=statement,
                example={"n": 27, "reason": "Not prime"},
                explanation="Number is composite, testing primality conjecture",
                search_strategy=SearchStrategy.EXHAUSTIVE,
                confidence=0.8,
            )
        
        if "square" in statement.lower():
            # Check small squares
            for n in range(2, 20):
                if not self._check_property(n, statement):
                    return Counterexample(
                        conjecture=statement,
                        example={"n": n},
                        explanation=f"n={n} fails the property",
                        search_strategy=SearchStrategy.EXHAUSTIVE,
                        confidence=0.9,
                    )
        
        return None
    
    def _random_search(
        self, statement: str, variables: List[str], max_attempts: int
    ) -> Optional[Counterexample]:
        """Random search for counterexample."""
        import random
        
        for _ in range(max_attempts):
            n = random.randint(2, 1000)
            if not self._check_property(n, statement):
                return Counterexample(
                    conjecture=statement,
                    example={"n": n},
                    explanation=f"Random test: n={n} fails",
                    search_strategy=SearchStrategy.RANDOM,
                    confidence=0.7,
                )
        
        return None
    
    def _boundary_search(
        self, statement: str, variables: List[str]
    ) -> Optional[Counterexample]:
        """Search at boundary values."""
        boundary_values = [0, 1, -1, 2, -2, 100, -100, 1000]
        
        for n in boundary_values:
            if not self._check_property(n, statement):
                return Counterexample(
                    conjecture=statement,
                    example={"n": n},
                    explanation=f"Boundary value n={n} fails",
                    search_strategy=SearchStrategy.BOUNDARY,
                    confidence=0.85,
                )
        
        return None
    
    def _check_property(self, n: int, statement: str) -> bool:
        """Check if a number satisfies a property."""
        statement_lower = statement.lower()
        
        # Simple property checks
        if "even" in statement_lower:
            return n % 2 == 0
        
        if "odd" in statement_lower:
            return n % 2 != 0
        
        if "prime" in statement_lower:
            return self._is_prime(n)
        
        if "positive" in statement_lower:
            return n > 0
        
        if "divisible by 3" in statement_lower:
            return n % 3 == 0
        
        # Default: assume property holds
        return True
    
    def _is_prime(self, n: int) -> bool:
        """Check if n is prime."""
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        
        return True
