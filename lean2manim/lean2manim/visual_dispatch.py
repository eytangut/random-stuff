from __future__ import annotations
from dataclasses import dataclass, field
from .proof_tree import Expr, GoalState, TacticStep


@dataclass
class VisualSpec:
    """Describes how to render an expression or tactic step."""
    encoding: str          # number_line | axis_region | venn | arrow_blob | squares | prop_and |
                           # prop_or | exists_container | forall_param | eq_bridge | generic_box
    label: str = ""
    sub_specs: list[VisualSpec] = field(default_factory=list)
    color: str = "#FFFFFF"
    anim_hint: str = ""    # fly_in | morph | rewrite_wash | split | spiral | snap | collapse |
                           # contradiction | fan_out | witness_snap | bridge_chain | none


# ── type category → encoding ──────────────────────────────────────────────────

_TYPE_ENCODING: dict[str, str] = {
    "Nat":      "number_line",
    "Int":      "number_line",
    "Real":     "axis_region",
    "Prop":     "generic_box",
    "Set":      "venn",
    "List":     "squares",
    "Function": "arrow_blob",
    "Group":    "arrow_blob",
    "Unknown":  "generic_box",
    "":         "generic_box",
}

_TACTIC_ANIM: dict[str, str] = {
    "intro":        "fly_in",
    "apply":        "morph",
    "rw":           "rewrite_wash",
    "rewrite":      "rewrite_wash",
    "cases":        "split",
    "rcases":       "split",
    "induction":    "spiral",
    "exact":        "snap",
    "rfl":          "snap",
    "simp":         "collapse",
    "norm_num":     "collapse",
    "ring":         "collapse",
    "contradiction":"contradiction",
    "constructor":  "fan_out",
    "use":          "witness_snap",
    "calc":         "bridge_chain",
    "omega":        "collapse",
    "linarith":     "collapse",
    "tauto":        "collapse",
    "decide":       "collapse",
}


def _expr_encoding(expr: Expr) -> str:
    if expr.kind == "eq":
        return "eq_bridge"
    if expr.kind == "and":
        return "prop_and"
    if expr.kind == "or":
        return "prop_or"
    if expr.kind == "forall":
        return "forall_param"
    if expr.kind == "exists":
        return "exists_container"
    return _TYPE_ENCODING.get(expr.type_category, "generic_box")


# ── style-specific encoding overrides ────────────────────────────────────────

# geometric: prefer visual/spatial representations
_GEOMETRIC_ENCODING: dict[str, str] = {
    "Nat":      "number_line",
    "Int":      "number_line",
    "Real":     "axis_region",
    "Prop":     "generic_box",
    "Set":      "venn",
    "List":     "squares",
    "Function": "arrow_blob",
    "Group":    "arrow_blob",
    "Unknown":  "generic_box",
    "":         "generic_box",
}

# algebraic: prefer symbolic/algebraic representations (eq_bridge for equalities)
_ALGEBRAIC_ENCODING: dict[str, str] = {
    "Nat":      "generic_box",
    "Int":      "generic_box",
    "Real":     "generic_box",
    "Prop":     "generic_box",
    "Set":      "generic_box",
    "List":     "squares",
    "Function": "arrow_blob",
    "Group":    "arrow_blob",
    "Unknown":  "generic_box",
    "":         "generic_box",
}


def _expr_encoding_for_style(expr: Expr, style: str) -> str:
    """Return the visual encoding for expr under the given style."""
    # expr-shape rules always take priority (eq_bridge, prop_and, etc.)
    if expr.kind == "eq":
        return "eq_bridge"
    if expr.kind == "and":
        return "prop_and"
    if expr.kind == "or":
        return "prop_or"
    if expr.kind == "forall":
        return "forall_param"
    if expr.kind == "exists":
        return "exists_container"
    if style == "geometric":
        return _GEOMETRIC_ENCODING.get(expr.type_category, "generic_box")
    if style == "algebraic":
        return _ALGEBRAIC_ENCODING.get(expr.type_category, "generic_box")
    # auto: same as geometric (type-based)
    return _TYPE_ENCODING.get(expr.type_category, "generic_box")


def goal_visual_spec(goal: GoalState, color: str = "#FFFFFF", style: str = "auto") -> VisualSpec:
    enc = _expr_encoding_for_style(goal.conclusion, style)
    label = _expr_label(goal.conclusion)
    sub = []
    if goal.conclusion.kind in ("eq", "and", "or"):
        for arg in goal.conclusion.args:
            sub.append(VisualSpec(
                encoding=_expr_encoding_for_style(arg, style),
                label=_expr_label(arg),
                color=color,
                anim_hint="none",
            ))
    return VisualSpec(encoding=enc, label=label, sub_specs=sub, color=color, anim_hint="none")


def tactic_anim_hint(step: TacticStep) -> str:
    return _TACTIC_ANIM.get(step.tactic, "none")


def _expr_label(expr: Expr) -> str:
    """Produce a human-readable math label (no tactic names)."""
    if expr.kind == "nat_lit":
        return expr.name
    if expr.kind == "const":
        return expr.name
    if expr.kind == "var":
        return expr.name
    if expr.kind == "eq":
        parts = [_expr_label(a) for a in expr.args]
        return " = ".join(parts) if parts else "_ = _"
    if expr.kind == "and":
        parts = [_expr_label(a) for a in expr.args]
        return " \\wedge ".join(parts) if parts else "_ \\wedge _"
    if expr.kind == "or":
        parts = [_expr_label(a) for a in expr.args]
        return " \\vee ".join(parts) if parts else "_ \\vee _"
    if expr.kind == "forall":
        binder = expr.name or "x"
        body = _expr_label(expr.args[0]) if expr.args else "P"
        return f"\\forall {binder},\\, {body}"
    if expr.kind == "exists":
        binder = expr.name or "x"
        body = _expr_label(expr.args[0]) if expr.args else "P"
        return f"\\exists {binder},\\, {body}"
    if expr.kind == "app":
        fn = _expr_label(expr.args[0]) if expr.args else "f"
        args = [_expr_label(a) for a in expr.args[1:]]
        return f"{fn}({', '.join(args)})" if args else fn
    if expr.kind == "lambda":
        binder = expr.name or "x"
        body = _expr_label(expr.args[0]) if expr.args else "e"
        return f"\\lambda {binder} \\mapsto {body}"
    return expr.name or expr.kind or "?"
