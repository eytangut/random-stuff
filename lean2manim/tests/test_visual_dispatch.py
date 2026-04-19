from lean2manim.visual_dispatch import goal_visual_spec, tactic_anim_hint, _expr_label
from lean2manim.proof_tree import Expr, GoalState, TacticStep


def test_nat_goal_gets_number_line():
    expr = Expr(kind="const", name="n", type_category="Nat", syntactic_role="conclusion")
    goal = GoalState(id="g0", conclusion=expr)
    spec = goal_visual_spec(goal)
    assert spec.encoding == "number_line"


def test_eq_goal_gets_eq_bridge():
    expr = Expr(kind="eq", name="", type_category="Prop", syntactic_role="conclusion",
                args=[Expr(kind="var", name="a"), Expr(kind="var", name="b")])
    goal = GoalState(id="g0", conclusion=expr)
    spec = goal_visual_spec(goal)
    assert spec.encoding == "eq_bridge"


def test_prop_goal_gets_generic_box():
    expr = Expr(kind="const", name="P", type_category="Prop", syntactic_role="conclusion")
    goal = GoalState(id="g0", conclusion=expr)
    spec = goal_visual_spec(goal)
    assert spec.encoding == "generic_box"


def test_set_goal_gets_venn():
    expr = Expr(kind="const", name="S", type_category="Set", syntactic_role="conclusion")
    goal = GoalState(id="g0", conclusion=expr)
    spec = goal_visual_spec(goal)
    assert spec.encoding == "venn"


def test_tactic_anim_hints():
    assert tactic_anim_hint(TacticStep(id=0, tactic="intro")) == "fly_in"
    assert tactic_anim_hint(TacticStep(id=1, tactic="induction")) == "spiral"
    assert tactic_anim_hint(TacticStep(id=2, tactic="exact")) == "snap"
    assert tactic_anim_hint(TacticStep(id=3, tactic="cases")) == "split"
    assert tactic_anim_hint(TacticStep(id=4, tactic="simp")) == "collapse"


def test_tactic_anim_unknown():
    assert tactic_anim_hint(TacticStep(id=0, tactic="mystery_tactic")) == "none"


def test_expr_label_forall():
    expr = Expr(kind="forall", name="n", args=[Expr(kind="const", name="P")])
    label = _expr_label(expr)
    assert "forall" in label or "∀" in label or "\\forall" in label
    assert "n" in label


def test_expr_label_eq():
    expr = Expr(kind="eq", name="", args=[Expr(kind="var", name="a"), Expr(kind="var", name="b")])
    label = _expr_label(expr)
    assert "a" in label
    assert "b" in label
    assert "=" in label


def test_expr_label_nat_lit():
    expr = Expr(kind="nat_lit", name="42")
    assert _expr_label(expr) == "42"


def test_eq_goal_has_sub_specs():
    expr = Expr(kind="eq", name="", args=[Expr(kind="var", name="a"), Expr(kind="var", name="b")])
    goal = GoalState(id="g0", conclusion=expr)
    spec = goal_visual_spec(goal)
    assert len(spec.sub_specs) == 2
