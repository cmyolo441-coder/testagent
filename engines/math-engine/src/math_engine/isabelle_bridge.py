"""Isabelle Bridge - Converts between internal proofs and Isabelle/HOL code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class IsabelleCode:
    """Isabelle/HOL code representation."""
    theorem_name: str
    statement: str
    proof_script: str
    imports: List[str]
    theory_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_name": self.theorem_name,
            "statement": self.statement,
            "proof_script": self.proof_script,
            "imports": self.imports,
            "theory_name": self.theory_name,
        }


class IsabelleBridge:
    """Converts between internal proofs and Isabelle/HOL code.
    
    Provides translation between the internal proof representation
    and Isabelle theorem prover syntax.
    """
    
    COMMON_IMPORTS = [
        "Main",
        "HOL-Library.Numeral_Syntax",
    ]
    
    def __init__(self):
        self._conversions: Dict[str, IsabelleCode] = {}
    
    def to_isabelle(self, proof: Dict[str, Any]) -> IsabelleCode:
        """Convert internal proof to Isabelle/HOL code.
        
        Args:
            proof: Internal proof representation
            
        Returns:
            IsabelleCode with Isabelle syntax
        """
        theorem_name = proof.get("theorem_name", "my_theorem")
        statement = proof.get("statement", "")
        steps = proof.get("steps", [])
        
        # Convert to Isabelle syntax
        isa_statement = self._convert_statement(statement)
        isa_proof = self._convert_proof(steps)
        imports = self._determine_imports(statement)
        
        code = IsabelleCode(
            theorem_name=theorem_name,
            statement=isa_statement,
            proof_script=isa_proof,
            imports=imports,
            theory_name="MyTheory",
        )
        
        self._conversions[theorem_name] = code
        return code
    
    def from_isabelle(self, code: str) -> Dict[str, Any]:
        """Convert Isabelle/HOL code to internal representation.
        
        Args:
            code: Isabelle code string
            
        Returns:
            Internal proof representation
        """
        lines = code.strip().split('\n')
        
        theorem_name = "unknown"
        statement = ""
        proof_steps = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("theorem") or line.startswith("lemma"):
                parts = line.split(":")
                theorem_name = parts[0].replace("theorem", "").replace("lemma", "").strip()
                statement = parts[1].strip().rstrip(':') if len(parts) > 1 else ""
            elif line.startswith("apply"):
                tactic = line.replace("apply", "").strip().strip('()')
                proof_steps.append({"type": "tactic", "tactic": tactic})
            elif line.startswith("done"):
                proof_steps.append({"type": "proof_end"})
            elif line.startswith("by"):
                proof_steps.append({"type": "by", "tactic": line})
        
        return {
            "theorem_name": theorem_name,
            "statement": statement,
            "steps": proof_steps,
            "source": "isabelle",
        }
    
    def _convert_statement(self, statement: str) -> str:
        """Convert mathematical statement to Isabelle syntax."""
        isa = statement
        
        # Replace common symbols
        replacements = {
            "∀": "∀",
            "∃": "∃",
            "→": "⟹",
            "∧": "∧",
            "∨": "∨",
            "¬": "¬",
            "=": "=",
            "≠": "≠",
            "≤": "≤",
            "≥": "≥",
            "∈": "∈",
        }
        
        for math_sym, isa_sym in replacements.items():
            isa = isa.replace(math_sym, isa_sym)
        
        return isa
    
    def _convert_proof(self, steps: List[Dict[str, Any]]) -> str:
        """Convert proof steps to Isabelle tactics."""
        if not steps:
            return "apply simp\n done"
        
        tactics = []
        for step in steps:
            step_type = step.get("type", "unknown")
            description = step.get("description", "")
            
            if step_type == "introduction":
                tactics.append("apply (intro allI)")
            elif step_type == "apply":
                tactics.append(f"apply (rule {description})")
            elif step_type == "simp":
                tactics.append("apply simp")
            elif step_type == "auto":
                tactics.append("apply auto")
            elif step_type == "metis":
                tactics.append("apply metis")
            else:
                tactics.append("apply simp")
        
        tactics.append("done")
        
        return "\n".join(tactics)
    
    def _determine_imports(self, statement: str) -> List[str]:
        """Determine required imports."""
        imports = list(self.COMMON_IMPORTS)
        
        statement_lower = statement.lower()
        
        if "list" in statement_lower:
            imports.append("HOL-List")
        
        if "nat" in statement_lower or "natural" in statement_lower:
            imports.append("Nat")
        
        return list(set(imports))
