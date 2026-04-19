import ast
import os
import tempfile
from pathlib import Path

from lean2manim.parser import parse_proof_tree
from lean2manim.emitter import emit_scene_file

SIMPLE_PROOF = {
    "theorem_name": "test_thm",
    "theorem_statement": "1 = 1",
    "steps": [
        {
            "id": 0,
            "tactic": "rfl",
            "tactic_args": [],
            "pre_goals": [{"id": "g0", "conclusion": {"kind": "eq", "name": "", "type_category": "Prop",
                           "syntactic_role": "conclusion", "args": []}, "hypotheses": []}],
            "post_goals": [],
            "hyp_added": [],
            "hyp_removed": []
        }
    ]
}


def test_emit_produces_python_file():
    pt = parse_proof_tree(SIMPLE_PROOF)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        assert "from manim import" in content
        assert "MovingCameraScene" in content
        assert "ProofScene" in content
        assert "HypothesisShelf" in content
        assert "construct" in content
        # Generated file must be valid Python
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_deterministic():
    pt = parse_proof_tree(SIMPLE_PROOF)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out1 = f.name
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out2 = f.name
    try:
        emit_scene_file(pt, out1)
        emit_scene_file(pt, out2)
        c1 = Path(out1).read_text()
        c2 = Path(out2).read_text()
        assert c1 == c2
        ast.parse(c1)
    finally:
        os.unlink(out1)
        os.unlink(out2)


def test_emit_contains_theorem_name():
    pt = parse_proof_tree(SIMPLE_PROOF)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        assert "test_thm" in content
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_with_intro_step():
    proof = {
        "theorem_name": "intro_test",
        "theorem_statement": "∀ n : ℕ, n = n",
        "steps": [
            {
                "id": 0,
                "tactic": "intro",
                "tactic_args": ["n"],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "forall", "name": "n",
                               "type_category": "Nat", "syntactic_role": "conclusion",
                               "args": [{"kind": "eq", "name": "", "type_category": "Prop",
                                         "syntactic_role": "conclusion", "args": []}]},
                               "hypotheses": []}],
                "post_goals": [{"id": "g1", "conclusion": {"kind": "eq", "name": "",
                                "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                                "hypotheses": []}],
                "hyp_added": [{"name": "n", "type_expr": {"kind": "const", "name": "Nat",
                                "type_category": "Nat", "syntactic_role": "hypothesis", "args": []}}],
                "hyp_removed": []
            },
            {
                "id": 1,
                "tactic": "rfl",
                "tactic_args": [],
                "pre_goals": [{"id": "g1", "conclusion": {"kind": "eq", "name": "",
                               "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        assert "fly_in" in content or "FadeIn" in content
        assert "intro_test" in content
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_with_induction_step():
    proof = {
        "theorem_name": "induction_test",
        "theorem_statement": "∀ n, P n",
        "steps": [
            {
                "id": 0,
                "tactic": "induction",
                "tactic_args": ["n"],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "forall", "name": "n",
                               "type_category": "Nat", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [
                    {"id": "g_base", "conclusion": {"kind": "const", "name": "P_zero",
                     "type_category": "Prop", "syntactic_role": "conclusion", "args": []}, "hypotheses": []},
                    {"id": "g_step", "conclusion": {"kind": "const", "name": "P_succ",
                     "type_category": "Prop", "syntactic_role": "conclusion", "args": []}, "hypotheses": []}
                ],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        assert "GrowFromCenter" in content or "spiral" in content
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_style_geometric():
    """--style geometric produces valid Python with number_line encoding for Nat goals."""
    proof = {
        "theorem_name": "geo_test",
        "theorem_statement": "n = n",
        "steps": [
            {
                "id": 0,
                "tactic": "rfl",
                "tactic_args": [],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "const", "name": "n",
                               "type_category": "Nat", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out, style="geometric")
        content = Path(out).read_text()
        assert "number_line" in content
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_special_chars_in_label():
    """Labels with quotes/newlines must not break the generated Python."""
    proof = {
        "theorem_name": 'thm_with_"quotes"',
        "theorem_statement": 'line1\nline2',
        "steps": [
            {
                "id": 0,
                "tactic": "rfl",
                "tactic_args": [],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "eq", "name": "",
                               "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        # Must parse without error despite special chars
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_node_var_special_chars():
    """Node ids with primes/dots/colons produce valid Python identifiers."""
    proof = {
        "theorem_name": "prime_test",
        "theorem_statement": "a' = a'",
        "steps": [
            {
                "id": 0,
                "tactic": "rfl",
                "tactic_args": [],
                "pre_goals": [{"id": "g0.sub:node'", "conclusion": {"kind": "eq", "name": "",
                               "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        ast.parse(content)
        # g0.sub:node' → all non-alphanumeric chars replaced with _ → node_g0_sub_node_
        assert "node_g0_sub_node_" in content
    finally:
        os.unlink(out)


def test_emit_hyp_removed_clears_shelf():
    """When hyp_removed is populated the generated code removes the item from the shelf."""
    proof = {
        "theorem_name": "clear_test",
        "theorem_statement": "∀ n : ℕ, True",
        "steps": [
            {
                "id": 0,
                "tactic": "intro",
                "tactic_args": ["n"],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "forall", "name": "n",
                               "type_category": "Nat", "syntactic_role": "conclusion",
                               "args": [{"kind": "const", "name": "True", "type_category": "Prop",
                                         "syntactic_role": "conclusion", "args": []}]},
                               "hypotheses": []}],
                "post_goals": [{"id": "g1", "conclusion": {"kind": "const", "name": "True",
                                "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                                "hypotheses": []}],
                "hyp_added": [{"name": "n", "type_expr": {"kind": "const", "name": "Nat",
                                "type_category": "Nat", "syntactic_role": "hypothesis", "args": []}}],
                "hyp_removed": []
            },
            {
                "id": 1,
                "tactic": "clear",
                "tactic_args": ["n"],
                "pre_goals": [{"id": "g1", "conclusion": {"kind": "const", "name": "True",
                               "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [{"id": "g2", "conclusion": {"kind": "const", "name": "True",
                                "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                                "hypotheses": []}],
                "hyp_added": [],
                "hyp_removed": ["n"]
            },
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        ast.parse(content)
        # The generated code must call shelf.remove_item with the hyp_0 shelf key
        assert "shelf.remove_item" in content
        assert "hyp_n_0" in content  # key = hyp_{name}_{step_id}
    finally:
        os.unlink(out)


def test_emit_real_goal_gets_axis_region():
    """Goals with type_category='Real' should use axis_region encoding in geometric style."""
    proof = {
        "theorem_name": "real_test",
        "theorem_statement": "x > 0",
        "steps": [
            {
                "id": 0,
                "tactic": "exact",
                "tactic_args": ["h"],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "const", "name": "x",
                               "type_category": "Real", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out, style="geometric")
        content = Path(out).read_text()
        assert "axis_region" in content
        ast.parse(content)
    finally:
        os.unlink(out)


def test_emit_generic_fallback_no_self_transform():
    """The generic animation branch uses a safe if-in-active_nodes guard, not a self-transform."""
    proof = {
        "theorem_name": "generic_test",
        "theorem_statement": "P",
        "steps": [
            {
                "id": 0,
                "tactic": "unknown_tactic",
                "tactic_args": [],
                "pre_goals": [{"id": "g0", "conclusion": {"kind": "const", "name": "P",
                               "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                               "hypotheses": []}],
                "post_goals": [{"id": "g1", "conclusion": {"kind": "const", "name": "P2",
                                "type_category": "Prop", "syntactic_role": "conclusion", "args": []},
                                "hypotheses": []}],
                "hyp_added": [],
                "hyp_removed": []
            }
        ]
    }
    pt = parse_proof_tree(proof)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, dir=".") as f:
        out = f.name
    try:
        emit_scene_file(pt, out)
        content = Path(out).read_text()
        ast.parse(content)
        # Should use the if-guard pattern, not .get()
        assert 'active_nodes.get(' not in content
        assert 'if "g0" in active_nodes' in content
    finally:
        os.unlink(out)

