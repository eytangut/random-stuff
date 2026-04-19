import json
import pytest
from lean2manim.parser import parse_proof_tree
from lean2manim.proof_tree import ProofTree, TacticStep


MINIMAL_PROOF = {
    "theorem_name": "test",
    "theorem_statement": "1 = 1",
    "steps": [
        {
            "id": 0,
            "tactic": "rfl",
            "tactic_args": [],
            "pre_goals": [{"id": "g0", "conclusion": {"kind": "eq", "name": "", "type_category": "Prop", "syntactic_role": "conclusion", "args": []}, "hypotheses": []}],
            "post_goals": [],
            "hyp_added": [],
            "hyp_removed": []
        }
    ]
}


def test_parse_basic():
    pt = parse_proof_tree(MINIMAL_PROOF)
    assert isinstance(pt, ProofTree)
    assert pt.theorem_name == "test"
    assert len(pt.steps) == 1
    assert pt.steps[0].tactic == "rfl"


def test_proof_hash_deterministic():
    pt1 = parse_proof_tree(MINIMAL_PROOF)
    pt2 = parse_proof_tree(MINIMAL_PROOF)
    assert pt1.proof_hash == pt2.proof_hash


def test_expr_identity_hash_stable():
    pt = parse_proof_tree(MINIMAL_PROOF)
    h1 = pt.steps[0].pre_goals[0].conclusion.identity_hash
    assert h1  # non-empty
    # re-parse gives same hash
    pt2 = parse_proof_tree(MINIMAL_PROOF)
    h2 = pt2.steps[0].pre_goals[0].conclusion.identity_hash
    assert h1 == h2


def test_parse_empty_steps():
    data = {"theorem_name": "empty", "theorem_statement": "True", "steps": []}
    pt = parse_proof_tree(data)
    assert pt.theorem_name == "empty"
    assert pt.steps == []


def test_parse_hyp():
    data = {
        "theorem_name": "hyp_test",
        "theorem_statement": "n = n",
        "steps": [{
            "id": 0,
            "tactic": "intro",
            "tactic_args": ["n"],
            "pre_goals": [],
            "post_goals": [],
            "hyp_added": [{"name": "n", "type_expr": {"kind": "const", "name": "Nat", "type_category": "Nat", "syntactic_role": "hypothesis", "args": []}}],
            "hyp_removed": []
        }]
    }
    pt = parse_proof_tree(data)
    assert len(pt.steps[0].hyp_added) == 1
    assert pt.steps[0].hyp_added[0].name == "n"
