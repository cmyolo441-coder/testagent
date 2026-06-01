"""Number Theory Lab - Explores number theoretic properties."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class NumberProperty(Enum):
    """Properties of numbers."""
    PRIME = "prime"
    COMPOSITE = "composite"
    PERFECT = "perfect"
    ABUNDANT = "abundant"
    DEFICIENT = "deficient"
    AMICABLE = "amicable"
    FIBONACCI = "fibonacci"
    TRIANGULAR = "triangular"
    SQUARE = "square"
    CUBE = "cube"


@dataclass
class NumberTheoreticResult:
    """Result of number theoretic analysis."""
    number: int
    properties: List[NumberProperty]
    prime_factorization: List[Tuple[int, int]]
    divisors: List[int]
    euler_totient: int
    mobius_function: int
    related_numbers: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "properties": [p.value for p in self.properties],
            "prime_factorization": [(p, e) for p, e in self.prime_factorization],
            "divisors": self.divisors,
            "euler_totient": self.euler_totient,
            "mobius_function": self.mobius_function,
            "related_numbers": self.related_numbers,
        }


class NumberTheoryLab:
    """Explores number theoretic properties.
    
    Provides tools for analyzing number theoretic properties,
    primality testing, and factorization.
    """
    
    def __init__(self):
        self._results: Dict[int, NumberTheoreticResult] = {}
        self._primes = self._sieve_of_eratosthenes(1000)
    
    def _sieve_of_eratosthenes(self, limit: int) -> List[int]:
        """Generate primes using sieve of Eratosthenes."""
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        
        for i in range(2, int(math.sqrt(limit)) + 1):
            if sieve[i]:
                for j in range(i*i, limit + 1, i):
                    sieve[j] = False
        
        return [i for i in range(2, limit + 1) if sieve[i]]
    
    def explore(self, number: int) -> NumberTheoreticResult:
        """Explore number theoretic properties of a number.
        
        Args:
            number: Number to analyze
            
        Returns:
            NumberTheoreticResult with properties
        """
        if number in self._results:
            return self._results[number]
        
        # Determine properties
        properties = self._determine_properties(number)
        
        # Prime factorization
        factorization = self._prime_factorization(number)
        
        # Divisors
        divisors = self._find_divisors(number)
        
        # Euler's totient
        totient = self._euler_totient(number)
        
        # Möbius function
        mobius = self._mobius_function(number)
        
        # Related numbers
        related = self._find_related_numbers(number)
        
        result = NumberTheoreticResult(
            number=number,
            properties=properties,
            prime_factorization=factorization,
            divisors=divisors,
            euler_totient=totient,
            mobius_function=mobius,
            related_numbers=related,
        )
        
        self._results[number] = result
        return result
    
    def _determine_properties(self, n: int) -> List[NumberProperty]:
        """Determine properties of a number."""
        properties = []
        
        if n < 2:
            return properties
        
        # Primality
        if self._is_prime(n):
            properties.append(NumberProperty.PRIME)
        else:
            properties.append(NumberProperty.COMPOSITE)
        
        # Perfect number
        if self._is_perfect(n):
            properties.append(NumberProperty.PERFECT)
        elif self._is_abundant(n):
            properties.append(NumberProperty.ABUNDANT)
        else:
            properties.append(NumberProperty.DEFICIENT)
        
        # Special sequences
        if self._is_fibonacci(n):
            properties.append(NumberProperty.FIBONACCI)
        
        if self._is_triangular(n):
            properties.append(NumberProperty.TRIANGULAR)
        
        sqrt = int(math.sqrt(n))
        if sqrt * sqrt == n:
            properties.append(NumberProperty.SQUARE)
        
        cbrt = round(n ** (1/3))
        if cbrt ** 3 == n:
            properties.append(NumberProperty.CUBE)
        
        return properties
    
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
    
    def _is_perfect(self, n: int) -> bool:
        """Check if n is a perfect number."""
        if n < 2:
            return False
        
        divisor_sum = sum(d for d in range(1, n) if n % d == 0)
        return divisor_sum == n
    
    def _is_abundant(self, n: int) -> bool:
        """Check if n is an abundant number."""
        if n < 2:
            return False
        
        divisor_sum = sum(d for d in range(1, n) if n % d == 0)
        return divisor_sum > n
    
    def _is_fibonacci(self, n: int) -> bool:
        """Check if n is a Fibonacci number."""
        if n < 0:
            return False
        
        a, b = 0, 1
        while b < n:
            a, b = b, a + b
        
        return b == n
    
    def _is_triangular(self, n: int) -> bool:
        """Check if n is a triangular number."""
        if n < 1:
            return False
        
        # n = k(k+1)/2, so k = (-1 + sqrt(1+8n))/2
        discriminant = 1 + 8 * n
        sqrt_disc = int(math.sqrt(discriminant))
        
        return sqrt_disc * sqrt_disc == discriminant
    
    def _prime_factorization(self, n: int) -> List[Tuple[int, int]]:
        """Compute prime factorization."""
        if n <= 1:
            return []
        
        factors = []
        
        for p in self._primes:
            if p * p > n:
                break
            
            if n % p == 0:
                count = 0
                while n % p == 0:
                    count += 1
                    n //= p
                factors.append((p, count))
        
        if n > 1:
            factors.append((n, 1))
        
        return factors
    
    def _find_divisors(self, n: int) -> List[int]:
        """Find all divisors of n."""
        if n <= 0:
            return []
        
        divisors = []
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                divisors.append(i)
                if i != n // i:
                    divisors.append(n // i)
        
        return sorted(divisors)
    
    def _euler_totient(self, n: int) -> int:
        """Compute Euler's totient function."""
        if n <= 0:
            return 0
        
        result = n
        p = 2
        
        temp = n
        while p * p <= temp:
            if temp % p == 0:
                while temp % p == 0:
                    temp //= p
                result -= result // p
            p += 1
        
        if temp > 1:
            result -= result // temp
        
        return result
    
    def _mobius_function(self, n: int) -> int:
        """Compute Möbius function."""
        if n <= 0:
            return 0
        
        if n == 1:
            return 1
        
        prime_factors = self._prime_factorization(n)
        
        # Check for square factors
        for p, e in prime_factors:
            if e > 1:
                return 0
        
        # (-1)^k where k is number of prime factors
        return (-1) ** len(prime_factors)
    
    def _find_related_numbers(self, n: int) -> Dict[str, int]:
        """Find related numbers."""
        related = {}
        
        # Twin primes
        if self._is_prime(n):
            if self._is_prime(n + 2):
                related["twin_prime"] = n + 2
            if self._is_prime(n - 2):
                related["twin_prime_minus"] = n - 2
        
        # Perfect number partner
        if self._is_perfect(n):
            related["sum_of_divisors"] = 2 * n
        
        # Fibonacci neighbors
        if self._is_fibonacci(n):
            a, b = 0, 1
            while b < n:
                a, b = b, a + b
            if b == n:
                related["next_fibonacci"] = b + a
        
        return related
