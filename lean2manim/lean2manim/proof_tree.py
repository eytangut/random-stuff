from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Expr:
    """A node in Lean's expression AST, annotated for visual use."""
    kind: str          # const | app | forall | exists | eq | and | or | nat_lit | var | lambda
    name: str = ""     # for const/var
    args: list[Expr] = field(default_factory=list)
    # Filled by the normalizer
    identity_hash: str = ""
    type_category: str = ""   # Nat | Int | Real | Prop | Set | List | Function | Group | Unknown
    syntactic_role: str = ""  # lhs | rhs | hypothesis | conclusion | bound_var | unknown

    def __post_init__(self):
        if not self.identity_hash:
            self.identity_hash = _hash_expr(self)


def _hash_expr(expr: Expr) -> str:
    payload = expr.kind + ":" + expr.name + ":" + ":".join(e.identity_hash or _hash_expr(e) for e in expr.args)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


@dataclass
class Hypothesis:
    name: str
    type_expr: Expr
    introduced_at_step: int = -1


@dataclass
class GoalState:
    id: str
    conclusion: Expr
    hypotheses: list[Hypothesis] = field(default_factory=list)


@dataclass
class TacticStep:
    id: int
    tactic: str
    tactic_args: list[str] = field(default_factory=list)
    pre_goals: list[GoalState] = field(default_factory=list)
    post_goals: list[GoalState] = field(default_factory=list)
    hyp_added: list[Hypothesis] = field(default_factory=list)
    hyp_removed: list[str] = field(default_factory=list)


@dataclass
class ProofTree:
    theorem_name: str
    theorem_statement: str
    proof_hash: str
    steps: list[TacticStep] = field(default_factory=list)
