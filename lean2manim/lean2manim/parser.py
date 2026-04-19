from __future__ import annotations
import json
import hashlib
from pathlib import Path
from .proof_tree import Expr, Hypothesis, GoalState, TacticStep, ProofTree


def parse_expr(d: dict) -> Expr:
    if d is None:
        return Expr(kind="unknown")
    args = [parse_expr(a) for a in d.get("args", [])]
    e = Expr(
        kind=d.get("kind", "unknown"),
        name=d.get("name", ""),
        args=args,
        type_category=d.get("type_category", ""),
        syntactic_role=d.get("syntactic_role", ""),
    )
    # recompute stable hash
    from .proof_tree import _hash_expr
    e.identity_hash = d.get("identity_hash") or _hash_expr(e)
    return e


def parse_hyp(d: dict, step_id: int = -1) -> Hypothesis:
    return Hypothesis(
        name=d["name"],
        type_expr=parse_expr(d.get("type_expr", {})),
        introduced_at_step=d.get("introduced_at_step", step_id),
    )


def parse_goal(d: dict) -> GoalState:
    return GoalState(
        id=d["id"],
        conclusion=parse_expr(d.get("conclusion", {})),
        hypotheses=[parse_hyp(h) for h in d.get("hypotheses", [])],
    )


def parse_step(d: dict) -> TacticStep:
    step_id = d.get("id", 0)
    return TacticStep(
        id=step_id,
        tactic=d.get("tactic", "unknown"),
        tactic_args=d.get("tactic_args", []),
        pre_goals=[parse_goal(g) for g in d.get("pre_goals", [])],
        post_goals=[parse_goal(g) for g in d.get("post_goals", [])],
        hyp_added=[parse_hyp(h, step_id) for h in d.get("hyp_added", [])],
        hyp_removed=d.get("hyp_removed", []),
    )


def parse_proof_tree(data: dict) -> ProofTree:
    theorem_name = data.get("theorem_name", "theorem")
    stmt = data.get("theorem_statement", "")
    # deterministic proof hash: SHA256 of the raw JSON
    raw = json.dumps(data, sort_keys=True)
    proof_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
    steps = [parse_step(s) for s in data.get("steps", [])]
    return ProofTree(
        theorem_name=theorem_name,
        theorem_statement=stmt,
        proof_hash=proof_hash,
        steps=steps,
    )


def load_proof_tree(path: str | Path) -> ProofTree:
    with open(path) as f:
        data = json.load(f)
    return parse_proof_tree(data)
