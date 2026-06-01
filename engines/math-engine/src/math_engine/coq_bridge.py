"""Coq Bridge - Converts between internal proofs and Coq code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class CoqCode:
    """Coq code representation."""
    theorem_name: str
    statement: str
    proof_script: str
    imports: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_name": self.theorem_name,
            "statement": self.statement,
            "proof_script": self.proof_script,
            "imports": self.imports,
        }


class CoqBridge:
    """Converts between internal proofs and Coq code.
    
    Provides translation between the internal proof representation
    and Coq theorem prover syntax.
    """
    
    COMMON_IMPORTS = [
        "Coq.Arith.Arith",
        "Coq.Lists.List",
        "Coq.ZArith.ZArith",
        "Coq.micromega.Lia",
    ]
    
    def __init__(self):
        self._conversions: Dict[str, CoqCode] = {}
    
    def to_coq(self, proof: Dict[str, Any]) -> CoqCode:
        """Convert internal proof to Coq code.
        
        Args:
            proof: Internal proof representation
            
        Returns:
            CoqCode with Coq syntax
        """
        theorem_name = proof.get("theorem_name", "my_theorem")
        statement = proof.get("statement", "")
        steps = proof.get("steps", [])
        
        # Convert to Coq syntax
        coq_statement = self._convert_statement(statement)
        coq_proof = self._convert_proof(steps)
        imports = self._determine_imports(statement)
        
        code = CoqCode(
            theorem_name=theorem_name,
            statement=coq_statement,
            proof_script=coq_proof,
            imports=imports,
        )
        
        self._conversions[theorem_name] = code
        return code
    
    def from_coq(self, code: str) -> Dict[str, Any]:
        """Convert Coq code to internal representation.
        
        Args:
            code: Coq code string
            
        Returns:
            Internal proof representation
        """
        lines = code.strip().split('\n')
        
        theorem_name = "unknown"
        statement = ""
        proof_steps = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("Theorem") or line.startswith("Lemma"):
                parts = line.split(":")
                theorem_name = parts[0].replace("Theorem", "").replace("Lemma", "").strip()
                statement = parts[1].strip().rstrip('.') if len(parts) > 1 else ""
            elif line.startswith("Proof"):
                proof_steps.append({"type": "proof_start"})
            elif line.startswith("Qed") or line.startswith("Admitted"):
                proof_steps.append({"type": "proof_end"})
            elif line and not line.startswith("(") and not line.startswith("*"):
                proof_steps.append({"type": "tactic", "tactic": line.rstrip('.')})
        
        return {
            "theorem_name": theorem_name,
            "statement": statement,
            "steps": proof_steps,
            "source": "coq",
        }
    
    def _convert_statement(self, statement: str) -> str:
        """Convert mathematical statement to Coq syntax."""
        coq = statement
        
        # Replace common symbols
        replacements = {
            "∀": "forall",
            "∃": "exists",
            "→": "->",
            "∧": "/\\",
            "∨": "\\/",
            "¬": "~",
            "=": "=",
            "≠": "<>",
            "≤": "<=",
            "≥": ">=",
            "∈": "In",
            "+": "+",
            "*": "*",
        }
        
        for math_sym, coq_sym in replacements.items():
            coq = coq.replace(math_sym, coq_sym)
        
        return coq
    
    def _convert_proof(self, steps: List[Dict[str, Any]]) -> str:
        """Convert proof steps to Coq tactics."""
        if not steps:
            return "Proof.\n  sorry.\nQed."
        
        tactics = ["Proof."]
        for step in steps:
            step_type = step.get("type", "unknown")
            description = step.get("description", "")
            
            if step_type == "introduction":
                tactics.append("  intros.")
            elif step_type == "apply":
                tactics.append(f"  apply {description}.")
            elif step_type == "rewrite":
                tactics.append(f"  rewrite {description}.")
            elif step_type == "omega":
                tactics.append("  omega.")
            elif step_type == "auto":
                tactics.append("  auto.")
            else:
                tactics.append("  admit.")
        
        tactics.append("Qed.")
        
        return "\n".join(tactics)
    
    def _determine_imports(self, statement: str) -> List[str]:
        """Determine required imports."""
        imports = list(self.COMMON_IMPORTS)
        
        statement_lower = statement.lower()
        
        if "nat" in statement_lower or "natural" in statement_lower:
            imports.append("Coq.Arith.Arith")
        
        if "list" in statement_lower:
            imports.append("Coq.Lists.List")
        
        return list(set(imports))
