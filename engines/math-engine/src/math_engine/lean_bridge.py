"""Lean Bridge - Converts between internal proofs and Lean 4 code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class LeanCode:
    """Lean 4 code representation."""
    theorem_name: str
    statement: str
    proof_term: str
    imports: List[str]
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_name": self.theorem_name,
            "statement": self.statement,
            "proof_term": self.proof_term,
            "imports": self.imports,
            "context": self.context,
        }


class LeanBridge:
    """Converts between internal proofs and Lean 4 code.
    
    Provides translation between the internal proof representation
    and Lean 4 theorem prover syntax.
    """
    
    # Common Lean imports
    COMMON_IMPORTS = [
        "Mathlib.Tactic",
        "Mathlib.Data.Nat.Basic",
        "Mathlib.Data.Int.Basic",
        "Mathlib.Algebra.Group.Basic",
    ]
    
    def __init__(self):
        self._conversions: Dict[str, LeanCode] = {}
    
    def to_lean(self, proof: Dict[str, Any]) -> LeanCode:
        """Convert internal proof to Lean 4 code.
        
        Args:
            proof: Internal proof representation
            
        Returns:
            LeanCode with Lean 4 syntax
        """
        theorem_name = proof.get("theorem_name", "my_theorem")
        statement = proof.get("statement", "")
        steps = proof.get("steps", [])
        
        # Convert statement to Lean syntax
        lean_statement = self._convert_statement(statement)
        
        # Convert proof steps
        lean_proof = self._convert_proof(steps)
        
        # Determine imports
        imports = self._determine_imports(statement, steps)
        
        # Generate context
        context = self._generate_context(theorem_name, lean_statement, lean_proof)
        
        code = LeanCode(
            theorem_name=theorem_name,
            statement=lean_statement,
            proof_term=lean_proof,
            imports=imports,
            context=context,
        )
        
        self._conversions[theorem_name] = code
        return code
    
    def from_lean(self, code: str) -> Dict[str, Any]:
        """Convert Lean 4 code to internal representation.
        
        Args:
            code: Lean 4 code string
            
        Returns:
            Internal proof representation
        """
        # Parse Lean code (simplified)
        lines = code.strip().split('\n')
        
        theorem_name = "unknown"
        statement = ""
        proof_steps = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("theorem"):
                parts = line.split(":")
                theorem_name = parts[0].replace("theorem", "").strip()
                statement = parts[1].strip() if len(parts) > 1 else ""
            elif line.startswith("by"):
                proof_steps.append({"type": "tactic", "tactic": line})
            elif line.startswith("sorry"):
                proof_steps.append({"type": "sorry", "description": "Incomplete proof"})
        
        return {
            "theorem_name": theorem_name,
            "statement": statement,
            "steps": proof_steps,
            "source": "lean",
        }
    
    def _convert_statement(self, statement: str) -> str:
        """Convert mathematical statement to Lean syntax."""
        # Simplified conversion
        lean = statement
        
        # Replace common math symbols
        replacements = {
            "∀": "∀",
            "∃": "∃",
            "→": "→",
            "∧": "∧",
            "∨": "∨",
            "¬": "¬",
            "=": "=",
            "≠": "≠",
            "≤": "≤",
            "≥": "≥",
            "∈": "∈",
            "∉": "∉",
            "∪": "∪",
            "∩": "∩",
        }
        
        for math_sym, lean_sym in replacements.items():
            lean = lean.replace(math_sym, lean_sym)
        
        return lean
    
    def _convert_proof(self, steps: List[Dict[str, Any]]) -> str:
        """Convert proof steps to Lean tactics."""
        if not steps:
            return "by sorry"
        
        tactics = []
        for step in steps:
            step_type = step.get("type", "unknown")
            description = step.get("description", "")
            
            if step_type == "introduction":
                tactics.append("intro h")
            elif step_type == "apply":
                tactics.append(f"apply {description}")
            elif step_type == "rewrite":
                tactics.append(f"rw [{description}]")
            elif step_type == "simp":
                tactics.append("simp")
            elif step_type == "omega":
                tactics.append("omega")
            else:
                tactics.append("sorry")
        
        if tactics:
            return "by\n  " + "\n  ".join(tactics)
        return "by sorry"
    
    def _determine_imports(self, statement: str, steps: List[Dict[str, Any]]) -> List[str]:
        """Determine required imports."""
        imports = list(self.COMMON_IMPORTS)
        
        statement_lower = statement.lower()
        
        if "nat" in statement_lower or "natural" in statement_lower:
            imports.append("Mathlib.Data.Nat.Basic")
        
        if "int" in statement_lower or "integer" in statement_lower:
            imports.append("Mathlib.Data.Int.Basic")
        
        if "group" in statement_lower or "ring" in statement_lower or "field" in statement_lower:
            imports.append("Mathlib.Algebra.Group.Basic")
        
        return list(set(imports))
    
    def _generate_context(
        self, theorem_name: str, statement: str, proof: str
    ) -> str:
        """Generate full Lean context."""
        context_parts = []
        
        context_parts.append("import Mathlib.Tactic\n")
        
        context_parts.append(f"/-- {theorem_name} --/")
        context_parts.append(f"theorem {theorem_name} : {statement} :=")
        context_parts.append(f"{proof}\n")
        
        return "\n".join(context_parts)
