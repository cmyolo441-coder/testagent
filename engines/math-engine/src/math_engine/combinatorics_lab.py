"""Combinatorics Lab - Explores combinatorial mathematical structures."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class StructureType(Enum):
    """Types of combinatorial structures."""
    PERMUTATION = "permutation"
    COMBINATION = "combination"
    PARTITION = "partition"
    GRAPH = "graph"
    TREE = "tree"
    LATTICE = "lattice"
    DESIGN = "design"


@dataclass
class CombinatorialStructure:
    """A combinatorial structure."""
    structure_type: StructureType
    size: int
    elements: List[Any]
    properties: Dict[str, Any]
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_type": self.structure_type.value,
            "size": self.size,
            "element_count": len(self.elements),
            "properties": self.properties,
            "count": self.count,
        }


@dataclass
class PermutationResult:
    """Result of permutation analysis."""
    n: int
    k: Optional[int]
    permutations: List[List[int]]
    count: int
    parity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "k": self.k,
            "permutation_count": len(self.permutations),
            "count": self.count,
            "parity": self.parity,
        }


@dataclass
class CombinationResult:
    """Result of combination analysis."""
    n: int
    k: int
    combinations: List[List[int]]
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "k": self.k,
            "combination_count": len(self.combinations),
            "count": self.count,
        }


class CombinatoricsLab:
    """Explores combinatorial mathematical structures.
    
    Provides tools for working with permutations, combinations,
    partitions, and other combinatorial objects.
    """
    
    def __init__(self):
        self._results: Dict[str, Any] = {}
        self._cache: Dict[str, int] = {}
    
    def explore(self, domain: str, parameters: Dict[str, Any] = None) -> CombinatorialStructure:
        """Explore combinatorial structures in a domain.
        
        Args:
            domain: Combinatorial domain
            parameters: Additional parameters
            
        Returns:
            CombinatorialStructure
        """
        params = parameters or {}
        
        domain_map = {
            "permutation": StructureType.PERMUTATION,
            "combination": StructureType.COMBINATION,
            "partition": StructureType.PARTITION,
            "graph": StructureType.GRAPH,
            "tree": StructureType.TREE,
        }
        
        structure_type = domain_map.get(domain.lower(), StructureType.PERMUTATION)
        size = params.get("size", 5)
        
        return CombinatorialStructure(
            structure_type=structure_type,
            size=size,
            elements=[],
            properties={"domain": domain},
            count=self._compute_count(structure_type, size, params),
        )
    
    def _compute_count(
        self, structure_type: StructureType, size: int, params: Dict[str, Any]
    ) -> int:
        """Compute count of structures."""
        if structure_type == StructureType.PERMUTATION:
            return math.factorial(size)
        elif structure_type == StructureType.COMBINATION:
            k = params.get("k", size // 2)
            return math.comb(size, k)
        elif structure_type == StructureType.PARTITION:
            return self._partition_function(size)
        else:
            return 0
    
    def _partition_function(self, n: int) -> int:
        """Compute partition function p(n)."""
        if n <= 0:
            return 1
        
        cache_key = f"p_{n}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Dynamic programming approach
        partitions = [0] * (n + 1)
        partitions[0] = 1
        
        for i in range(1, n + 1):
            for j in range(i, n + 1):
                partitions[j] += partitions[j - i]
        
        result = partitions[n]
        self._cache[cache_key] = result
        return result
    
    def generate_permutations(
        self, n: int, k: Optional[int] = None
    ) -> PermutationResult:
        """Generate permutations.
        
        Args:
            n: Size of set
            k: Size of permutation (optional, defaults to n)
            
        Returns:
            PermutationResult with permutations
        """
        if k is None:
            k = n
        
        # Generate permutations
        permutations = self._generate_perm_helper(list(range(n)), k)
        
        # Determine parity
        parity = "even" if len(permutations) % 2 == 0 else "odd"
        
        return PermutationResult(
            n=n,
            k=k,
            permutations=permutations,
            count=len(permutations),
            parity=parity,
        )
    
    def _generate_perm_helper(self, elements: List[int], k: int) -> List[List[int]]:
        """Generate permutations recursively."""
        if k == 0:
            return [[]]
        
        if not elements:
            return []
        
        result = []
        for i, elem in enumerate(elements):
            remaining = elements[:i] + elements[i+1:]
            for perm in self._generate_perm_helper(remaining, k - 1):
                result.append([elem] + perm)
        
        return result
    
    def generate_combinations(
        self, n: int, k: int
    ) -> CombinationResult:
        """Generate combinations.
        
        Args:
            n: Size of set
            k: Size of combination
            
        Returns:
            CombinationResult with combinations
        """
        combinations = self._generate_comb_helper(list(range(n)), k)
        
        return CombinationResult(
            n=n,
            k=k,
            combinations=combinations,
            count=len(combinations),
        )
    
    def _generate_comb_helper(self, elements: List[int], k: int) -> List[List[int]]:
        """Generate combinations recursively."""
        if k == 0:
            return [[]]
        
        if not elements:
            return []
        
        result = []
        for i in range(len(elements)):
            elem = elements[i]
            remaining = elements[i+1:]
            for comb in self._generate_comb_helper(remaining, k - 1):
                result.append([elem] + comb)
        
        return result
    
    def catalan_number(self, n: int) -> int:
        """Compute nth Catalan number."""
        if n <= 0:
            return 1
        
        return math.comb(2*n, n) // (n + 1)
    
    def bell_number(self, n: int) -> int:
        """Compute nth Bell number."""
        if n <= 0:
            return 1
        
        # Use Bell triangle
        bell = [[0] * (n + 1) for _ in range(n + 1)]
        bell[0][0] = 1
        
        for i in range(1, n + 1):
            bell[i][0] = bell[i-1][i-1]
            for j in range(1, i + 1):
                bell[i][j] = bell[i][j-1] + bell[i-1][j-1]
        
        return bell[n][0]
