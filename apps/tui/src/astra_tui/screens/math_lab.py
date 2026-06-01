"""Math Lab Screen — Proof explorer and conjecture management"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Conjecture:
    id: str = ""
    statement: str = ""
    description: str = ""
    status: str = "open"  # open, proven, disproven, undecidable, abandoned
    confidence: float = 0.5
    formalization: str = ""
    proof_id: Optional[str] = None
    domain: str = ""
    related_conjectures: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Proof:
    id: str = ""
    conjecture_id: str = ""
    title: str = ""
    method: str = ""  # direct, contradiction, induction, construction, computational
    status: str = "draft"  # draft, complete, verified, flawed
    steps: list[str] = field(default_factory=list)
    lemmas_used: list[str] = field(default_factory=list)
    confidence: float = 0.5
    verifier: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_at: Optional[str] = None


@dataclass
class Lemma:
    id: str = ""
    statement: str = ""
    proof_id: Optional[str] = None
    verified: bool = False


class MathLabScreen:
    """Proof explorer and conjecture management screen."""

    TITLE = "Math Lab"

    def __init__(self):
        self.conjectures: dict[str, Conjecture] = {}
        self.proofs: dict[str, Proof] = {}
        self.lemmas: dict[str, Lemma] = {}
        self.selected_conjecture_id: Optional[str] = None

    def state_conjecture(self, statement: str, description: str = "",
                         domain: str = "general", confidence: float = 0.5,
                         formalization: str = "", tags: list[str] = None) -> Conjecture:
        conj_id = f"CONJ-{len(self.conjectures) + 1:04d}"
        conjecture = Conjecture(
            id=conj_id,
            statement=statement,
            description=description,
            domain=domain,
            confidence=confidence,
            formalization=formalization,
            tags=tags or [],
        )
        self.conjectures[conj_id] = conjecture
        return conjecture

    def add_proof(self, conjecture_id: str, title: str, method: str = "direct",
                  steps: list[str] = None) -> Optional[Proof]:
        if conjecture_id not in self.conjectures:
            return None
        proof_id = f"PROOF-{len(self.proofs) + 1:04d}"
        proof = Proof(
            id=proof_id,
            conjecture_id=conjecture_id,
            title=title,
            method=method,
            steps=steps or [],
        )
        self.proofs[proof_id] = proof
        self.conjectures[conjecture_id].proof_id = proof_id
        return proof

    def add_step(self, proof_id: str, step: str) -> bool:
        proof = self.proofs.get(proof_id)
        if not proof:
            return False
        proof.steps.append(step)
        return True

    def complete_proof(self, proof_id: str) -> Optional[Proof]:
        proof = self.proofs.get(proof_id)
        if not proof:
            return None
        proof.status = "complete"
        conjecture = self.conjectures.get(proof.conjecture_id)
        if conjecture:
            conjecture.status = "proven"
        return proof

    def verify_proof(self, proof_id: str, verifier: str = "",
                     confidence: float = 1.0) -> Optional[Proof]:
        proof = self.proofs.get(proof_id)
        if not proof:
            return None
        proof.status = "verified"
        proof.verifier = verifier
        proof.confidence = confidence
        proof.verified_at = datetime.now(timezone.utc).isoformat()
        return proof

    def disprove_conjecture(self, conjecture_id: str) -> Optional[Conjecture]:
        conjecture = self.conjectures.get(conjecture_id)
        if not conjecture:
            return None
        conjecture.status = "disproven"
        return conjecture

    def add_lemma(self, statement: str, verified: bool = False) -> Lemma:
        lemma_id = f"LEM-{len(self.lemmas) + 1:04d}"
        lemma = Lemma(id=lemma_id, statement=statement, verified=verified)
        self.lemmas[lemma_id] = lemma
        return lemma

    def get_open_conjectures(self) -> list[Conjecture]:
        return [c for c in self.conjectures.values() if c.status == "open"]

    def get_proven_conjectures(self) -> list[Conjecture]:
        return [c for c in self.conjectures.values() if c.status == "proven"]

    def get_incomplete_proofs(self) -> list[Proof]:
        return [p for p in self.proofs.values() if p.status == "draft"]

    def get_proof_chain(self, conjecture_id: str) -> list[dict]:
        chain = []
        for proof in self.proofs.values():
            if proof.conjecture_id == conjecture_id:
                chain.append({
                    "proof_id": proof.id,
                    "title": proof.title,
                    "method": proof.method,
                    "status": proof.status,
                    "step_count": len(proof.steps),
                })
        return chain

    def render_header(self) -> str:
        conj = len(self.conjectures)
        proofs = len(self.proofs)
        proven = len(self.get_proven_conjectures())
        return f"╔══════════════════════════════════════════════════════════╗\n║ MATH LAB — {conj} conjectures, {proofs} proofs ({proven} proven){'':<11}║\n╚══════════════════════════════════════════════════════════╝"

    def render_conjectures(self) -> str:
        lines = ["┌─ Conjectures ───────────────────────────────────────┐"]
        status_icons = {"open": "○", "proven": "●", "disproven": "✗", "abandoned": "-"}
        for c in list(self.conjectures.values())[:6]:
            icon = status_icons.get(c.status, "?")
            lines.append(f"│ {icon} {c.statement[:40]:<40} {c.domain[:8]:<8} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_proofs(self) -> str:
        lines = ["┌─ Proofs ────────────────────────────────────────────┐"]
        for p in list(self.proofs.values())[:5]:
            status_icon = {"draft": "○", "complete": "◐", "verified": "●", "flawed": "✗"}.get(p.status, "?")
            lines.append(f"│ {status_icon} {p.title[:30]:<30} {p.method:<12} │")
        lines.append("└────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    def render_full(self) -> str:
        parts = [
            self.render_header(),
            "",
            self.render_conjectures(),
            "",
            self.render_proofs(),
        ]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "total_conjectures": len(self.conjectures),
            "total_proofs": len(self.proofs),
            "proven": len(self.get_proven_conjectures()),
            "open": len(self.get_open_conjectures()),
            "total_lemmas": len(self.lemmas),
        }
