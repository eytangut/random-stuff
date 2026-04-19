from __future__ import annotations
import io
import math
import re

from .proof_tree import ProofTree
from .colors import expr_color, var_color
from .visual_dispatch import goal_visual_spec, tactic_anim_hint
from .layout import ForceLayout

# Number of tactic steps between recap camera pull-back breaths
RECAP_FREQUENCY = 10


# ── Inlined class definitions written verbatim into the generated scene file ──

_INLINE_CLASSES = r'''
# ── Palette ───────────────────────────────────────────────────────────────────
PALETTE = ["#58C4DD","#83C167","#FC6255","#FFFF00","#C3A0F0","#FF862F","#1BBC9B","#FF77A8"]

def _palette(s: str) -> str:
    import hashlib
    h = int(hashlib.md5(s.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


# ── ProofNode ─────────────────────────────────────────────────────────────────

class ProofNode(VGroup):
    """A labeled rectangle representing a proof goal or hypothesis."""
    def __init__(self, label: str, encoding: str, color: str = WHITE, **kwargs):
        super().__init__(**kwargs)
        self.encoding = encoding
        self._label_str = label
        col = color

        safe_label = label if label else "?"

        if encoding == "number_line":
            try:
                line = NumberLine(x_range=[-3, 3, 1], length=4, color=col)
                dot = Dot(color=col).move_to(line.n2p(0))
                tex = MathTex(safe_label, color=col).next_to(dot, UP, buff=0.15)
                self.add(line, dot, tex)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "eq_bridge":
            try:
                parts = safe_label.split(" = ")
                left = MathTex(parts[0] if parts else "a", color=col)
                right = MathTex(parts[-1] if len(parts) > 1 else "b", color=col)
                right.next_to(left, RIGHT, buff=1.2)
                bridge = Line(left.get_right(), right.get_left(), color=col)
                eq = MathTex("=", color=col).move_to(bridge.get_center())
                self.add(left, bridge, eq, right)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "prop_and":
            try:
                parts = safe_label.split(" \\wedge ")
                if len(parts) < 2:
                    parts = [safe_label, "?"]
                boxes = VGroup(*[
                    VGroup(
                        RoundedRectangle(width=1.8, height=0.8, corner_radius=0.1,
                                         color=col, fill_opacity=0.15),
                        MathTex(p, color=col).scale(0.7)
                    ).arrange(ORIGIN) for p in parts[:2]
                ]).arrange(RIGHT, buff=0.5)
                bracket = Brace(boxes, direction=DOWN, color=col)
                sym = MathTex(r"\wedge", color=col).next_to(bracket, DOWN, buff=0.1)
                self.add(boxes, bracket, sym)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "prop_or":
            try:
                parts = safe_label.split(" \\vee ")
                if len(parts) < 2:
                    parts = [safe_label, "?"]
                left_box = VGroup(
                    RoundedRectangle(width=1.8, height=0.8, corner_radius=0.1,
                                     color=col, fill_opacity=0.15),
                    MathTex(parts[0], color=col).scale(0.7)
                ).arrange(ORIGIN)
                right_box = VGroup(
                    RoundedRectangle(width=1.8, height=0.8, corner_radius=0.1,
                                     color=col, fill_opacity=0.15),
                    MathTex(parts[-1], color=col).scale(0.7)
                ).arrange(ORIGIN)
                group = VGroup(left_box, right_box).arrange(RIGHT, buff=0.8)
                sym = MathTex(r"\vee", color=col).move_to(group.get_center())
                self.add(group, sym)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "venn":
            try:
                outer = Circle(radius=1.0, color=col, fill_opacity=0.1)
                dot = Dot(color=col, radius=0.1).shift(RIGHT * 0.3 + UP * 0.2)
                tex = MathTex(safe_label, color=col).scale(0.7).next_to(outer, UP, buff=0.1)
                self.add(outer, dot, tex)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "squares":
            try:
                chars = safe_label.split() if " " in safe_label else list(safe_label[:6])
                if not chars:
                    chars = ["?"]
                squares = VGroup(*[
                    VGroup(
                        Square(side_length=0.6, color=col, fill_opacity=0.15),
                        Text(c, font_size=18, color=col)
                    ).arrange(ORIGIN) for c in chars[:6]
                ]).arrange(RIGHT, buff=0.05)
                self.add(squares)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "arrow_blob":
            try:
                src = Ellipse(width=1.2, height=0.7, color=col, fill_opacity=0.15)
                dst = Ellipse(width=1.2, height=0.7, color=col, fill_opacity=0.15)
                VGroup(src, dst).arrange(RIGHT, buff=1.0)
                arr = Arrow(src.get_right(), dst.get_left(), color=col, buff=0.1)
                tex = MathTex(safe_label, color=col).scale(0.6).next_to(arr, UP, buff=0.1)
                self.add(src, arr, dst, tex)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "exists_container":
            try:
                box = RoundedRectangle(width=2.5, height=1.2, corner_radius=0.15, color=col,
                                       fill_opacity=0.1, stroke_width=2)
                inner = Dot(color=col, radius=0.15).move_to(box.get_center())
                tex = MathTex(safe_label, color=col).scale(0.65).next_to(box, UP, buff=0.1)
                self.add(box, inner, tex)
            except Exception:
                self._fallback(safe_label, col)
        elif encoding == "forall_param":
            try:
                slider_line = Line(LEFT * 1.2, RIGHT * 1.2, color=col)
                handle = Triangle(fill_color=col, fill_opacity=0.8, stroke_width=0).scale(0.12)
                handle.move_to(slider_line.get_start() + RIGHT * 0.4)
                tex = MathTex(safe_label, color=col).scale(0.65).next_to(slider_line, UP, buff=0.15)
                self.add(slider_line, handle, tex)
            except Exception:
                self._fallback(safe_label, col)
        else:  # generic_box
            self._fallback(safe_label, col)

    def _fallback(self, label: str, col) -> None:
        box = RoundedRectangle(
            width=max(len(label) * 0.18 + 0.6, 1.4),
            height=0.9, corner_radius=0.12,
            color=col, fill_opacity=0.12, stroke_width=2
        )
        try:
            tex = MathTex(label if label else "?", color=col).scale(0.65).move_to(box)
        except Exception:
            tex = Text(label[:20] if label else "?", font_size=16, color=col).move_to(box)
        self.add(box, tex)


# ── HypothesisShelf ───────────────────────────────────────────────────────────

class HypothesisShelf(VGroup):
    """Persistent bottom bar showing all active hypotheses."""
    SHELF_Y = -3.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items: dict[str, VMobject] = {}
        bg = Rectangle(width=14, height=1.1, fill_color="#0D0D1A", fill_opacity=0.85,
                       stroke_color="#333355", stroke_width=1)
        bg.move_to([0, self.SHELF_Y, 0])
        self.bg = bg
        self.add(bg)

    def add_item(self, key: str, mob: VMobject) -> None:
        mob.scale(0.42)
        self._items[key] = mob
        self._repack()
        if mob not in self.submobjects:
            self.add(mob)

    def remove_item(self, key: str) -> VMobject | None:
        mob = self._items.pop(key, None)
        if mob and mob in self.submobjects:
            self.remove(mob)
            self._repack()
        return mob

    def _repack(self) -> None:
        items = list(self._items.values())
        if not items:
            return
        total_w = sum(m.width for m in items) + 0.3 * (len(items) - 1)
        x = -total_w / 2
        for m in items:
            m.move_to([x + m.width / 2, self.SHELF_Y, 0])
            x += m.width + 0.3


# ── TacticArrow ───────────────────────────────────────────────────────────────

class TacticArrow(VGroup):
    """Curved arrow between two proof nodes."""
    def __init__(self, start: np.ndarray, end: np.ndarray, color: str = WHITE, **kwargs):
        super().__init__(**kwargs)
        arr = CurvedArrow(start, end, color=color, stroke_width=2)
        self.add(arr)
'''


def _safe_label(label: str) -> str:
    """Escape a label for safe embedding in a double-quoted Python string literal."""
    return (
        label
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _pos_str(pos: tuple[float, float]) -> str:
    return f"[{pos[0]:.4f}, {pos[1]:.4f}, 0]"


def _node_var(node_id: str) -> str:
    """Sanitize a node id into a valid Python identifier.

    Replaces any character that is not alphanumeric or underscore with ``_``,
    and prepends ``node_`` so the result can never start with a digit.
    """
    sanitized = re.sub(r"[^0-9A-Za-z_]", "_", node_id)
    return "node_" + sanitized


def _build_positions(proof_tree: ProofTree) -> dict[str, tuple[float, float]]:
    """
    Pre-compute all node positions by simulating the scene graph incrementally
    using ForceLayout. Returns final positions keyed by node_id.
    """
    layout = ForceLayout(proof_tree.proof_hash)
    all_node_ids: list[str] = []
    all_edges: list[tuple[str, str]] = []
    positions: dict[str, tuple[float, float]] = {}

    # Collect all node ids from the proof steps
    seen_goals: set[str] = set()
    seen_hyps: set[str] = set()

    for step in proof_tree.steps:
        for goal in step.pre_goals + step.post_goals:
            if goal.id not in seen_goals:
                seen_goals.add(goal.id)
                all_node_ids.append(goal.id)
        for hyp in step.hyp_added:
            hyp_id = f"hyp_{hyp.name}_{step.id}"
            if hyp_id not in seen_hyps:
                seen_hyps.add(hyp_id)
                all_node_ids.append(hyp_id)
        for pre in step.pre_goals:
            for post in step.post_goals:
                all_edges.append((pre.id, post.id))

    if all_node_ids:
        positions = layout.run(all_node_ids, all_edges)
    return positions


def emit_scene_file(proof_tree: ProofTree, output_path: str, style: str = "auto") -> None:
    """Write a complete runnable Manim scene file to output_path.

    Args:
        proof_tree: Parsed proof structure.
        output_path: Destination ``.py`` file path.
        style: Visual style — ``"auto"`` (type-based dispatch), ``"geometric"``
               (prefer spatial representations like number lines and Venn diagrams),
               or ``"algebraic"`` (prefer symbolic boxes and bridges).
    """
    positions = _build_positions(proof_tree)
    buf = io.StringIO()

    # ── Header ────────────────────────────────────────────────────────────────
    buf.write(f"# AUTO-GENERATED by lean2manim — DO NOT EDIT\n")
    buf.write(f"# proof: {proof_tree.theorem_name} (hash: {proof_tree.proof_hash})\n")
    buf.write(f"# style: {style}\n\n")
    buf.write("from manim import *\n")
    buf.write("import math\n")
    buf.write("import hashlib\n\n")

    # ── Inline classes ────────────────────────────────────────────────────────
    buf.write(_INLINE_CLASSES)
    buf.write("\n\n")

    # ── ProofScene class header ───────────────────────────────────────────────
    buf.write("class ProofScene(MovingCameraScene):\n")
    buf.write("    def construct(self):\n")
    ind = "        "  # 8-space indent inside construct

    # ── 1. Theorem header ─────────────────────────────────────────────────────
    thm_name = _safe_label(proof_tree.theorem_name)
    safe_stmt = _safe_label(proof_tree.theorem_statement)
    buf.write(f'{ind}# ── Theorem header ──\n')
    buf.write(f'{ind}header = Text("{thm_name}", font_size=36, color=WHITE)\n')
    buf.write(f'{ind}stmt = Text("{safe_stmt}", font_size=18, color=ManimColor("#A0A0A0"))\n')
    buf.write(f'{ind}VGroup(header, stmt).arrange(DOWN, buff=0.2).to_edge(UP, buff=0.3)\n')
    buf.write(f'{ind}self.play(Write(header), run_time=1.0)\n')
    buf.write(f'{ind}self.play(Write(stmt), run_time=0.8)\n')
    buf.write(f'{ind}self.play(header.animate.scale(0.5).to_corner(UL), stmt.animate.set_opacity(0.4), run_time=0.7)\n')
    buf.write(f'\n')

    # ── 2. Shelf ──────────────────────────────────────────────────────────────
    buf.write(f'{ind}# ── Hypothesis shelf ──\n')
    buf.write(f'{ind}shelf = HypothesisShelf()\n')
    buf.write(f'{ind}self.add(shelf)\n')
    buf.write(f'\n')

    # ── 3. Active nodes dict ───────────────────────────────────────────────────
    buf.write(f'{ind}# ── Active proof nodes on screen ──\n')
    buf.write(f'{ind}active_nodes: dict[str, ProofNode] = {{}}\n')
    buf.write(f'\n')

    # ── Emit initial goals from first step's pre_goals ────────────────────────
    initial_goals_emitted: set[str] = set()
    if proof_tree.steps and proof_tree.steps[0].pre_goals:
        first_goal = proof_tree.steps[0].pre_goals[0]
        if first_goal.id not in initial_goals_emitted:
            initial_goals_emitted.add(first_goal.id)
            pos = positions.get(first_goal.id, (0.0, 0.5))
            color = expr_color(first_goal.conclusion.identity_hash)
            spec = goal_visual_spec(first_goal, color, style=style)
            label = _safe_label(spec.label or first_goal.id)
            vname = _node_var(first_goal.id)
            buf.write(f'{ind}# Initial goal: {first_goal.id}\n')
            buf.write(f'{ind}{vname} = ProofNode("{label}", "{spec.encoding}", "{color}")\n')
            buf.write(f'{ind}{vname}.move_to({_pos_str(pos)})\n')
            buf.write(f'{ind}self.play(FadeIn({vname}), run_time=0.8)\n')
            buf.write(f'{ind}active_nodes["{first_goal.id}"] = {vname}\n')
            buf.write(f'\n')

    # ── 4. Tactic steps ───────────────────────────────────────────────────────
    emitted_goals: set[str] = set(initial_goals_emitted)
    step_count = 0

    for step in proof_tree.steps:
        step_count += 1
        anim = tactic_anim_hint(step)
        tactic_display = step.tactic + (
            (" " + " ".join(step.tactic_args)) if step.tactic_args else ""
        )
        buf.write(f'{ind}# ── Step {step.id}: {tactic_display} ({anim}) ──\n')

        # Identify active pre-goal (first pre-goal that is on screen)
        active_pre_goal_id: str | None = None
        for g in step.pre_goals:
            if g.id in emitted_goals:
                active_pre_goal_id = g.id
                break

        # Determine camera width based on animation type
        cam_width = 8
        if anim in ("split", "spiral", "fan_out"):
            cam_width = 12

        # Handle different animation types
        if anim == "fly_in":
            # intro: new hypothesis flies in
            for hyp in step.hyp_added:
                hyp_id = f"hyp_{hyp.name}_{step.id}"
                hyp_color = var_color(hyp.name)
                hyp_pos = positions.get(hyp_id, (-3.0, 1.0))
                hyp_label = _safe_label(hyp.name)
                hyp_vname = _node_var(hyp_id)
                buf.write(f'{ind}{hyp_vname} = ProofNode("{hyp_label}", "generic_box", "{hyp_color}")\n')
                buf.write(f'{ind}{hyp_vname}.move_to({_pos_str(hyp_pos)})\n')
                buf.write(f'{ind}self.play(FadeIn({hyp_vname}, shift=RIGHT*0.5), run_time=0.6)\n')
                buf.write(f'{ind}active_nodes["{hyp_id}"] = {hyp_vname}\n')
                # Copy to shelf
                buf.write(f'{ind}_shelf_copy_{hyp_vname} = {hyp_vname}.copy()\n')
                buf.write(f'{ind}shelf.add_item("{hyp_id}", _shelf_copy_{hyp_vname})\n')
            # Camera on pre-goal
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.5)\n')
            # Post goals appear (goal transforms as hypothesis is introduced)
            for pg in step.post_goals:
                if pg.id not in emitted_goals:
                    emitted_goals.add(pg.id)
                    pg_pos = positions.get(pg.id, (0.0, 0.5))
                    pg_color = expr_color(pg.conclusion.identity_hash)
                    pg_spec = goal_visual_spec(pg, pg_color, style=style)
                    pg_label = _safe_label(pg_spec.label or pg.id)
                    pg_vname = _node_var(pg.id)
                    buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                    buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                    if active_pre_goal_id and active_pre_goal_id in emitted_goals:
                        pre_vname = _node_var(active_pre_goal_id)
                        buf.write(f'{ind}self.play(Transform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.6)\n')
                        buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    else:
                        buf.write(f'{ind}self.play(FadeIn({pg_vname}), run_time=0.6)\n')
                    buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')

        elif anim == "snap":
            # exact/rfl: goal closes with a flash
            if active_pre_goal_id:
                pre_vname = _node_var(active_pre_goal_id)
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                flash_color = expr_color(
                    step.pre_goals[0].conclusion.identity_hash if step.pre_goals else ""
                )
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                buf.write(f'{ind}self.play(Flash(active_nodes["{active_pre_goal_id}"], color="{flash_color}"), run_time=0.5)\n')
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.4)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
            buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "collapse":
            # simp/norm_num/ring/omega etc: goal collapses, new simplified form appears
            if active_pre_goal_id:
                pre_vname = _node_var(active_pre_goal_id)
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                if step.post_goals:
                    # Simplified to new goals
                    for pg in step.post_goals:
                        if pg.id not in emitted_goals:
                            emitted_goals.add(pg.id)
                            pg_pos = positions.get(pg.id, (0.0, 0.5))
                            pg_color = expr_color(pg.conclusion.identity_hash)
                            pg_spec = goal_visual_spec(pg, pg_color, style=style)
                            pg_label = _safe_label(pg_spec.label or pg.id)
                            pg_vname = _node_var(pg.id)
                            buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                            buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                            buf.write(f'{ind}self.play(Transform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.7)\n')
                            buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                            buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
                else:
                    # Goal resolved
                    buf.write(f'{ind}self.play(ScaleInPlace(active_nodes["{active_pre_goal_id}"], 0), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "rewrite_wash":
            # rw: highlight then transform
            if active_pre_goal_id:
                pre_vname = _node_var(active_pre_goal_id)
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                buf.write(f'{ind}self.play(Indicate(active_nodes["{active_pre_goal_id}"], scale_factor=1.2), run_time=0.5)\n')
                if step.post_goals:
                    for pg in step.post_goals:
                        if pg.id not in emitted_goals:
                            emitted_goals.add(pg.id)
                            pg_pos = positions.get(pg.id, (0.0, 0.5))
                            pg_color = expr_color(pg.conclusion.identity_hash)
                            pg_spec = goal_visual_spec(pg, pg_color, style=style)
                            pg_label = _safe_label(pg_spec.label or pg.id)
                            pg_vname = _node_var(pg.id)
                            buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                            buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                            buf.write(f'{ind}self.play(Transform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.8)\n')
                            buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                            buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
                else:
                    buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "morph":
            # apply: transform goal with an arrow flash
            if active_pre_goal_id:
                pre_vname = _node_var(active_pre_goal_id)
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                if step.post_goals:
                    for pg in step.post_goals:
                        if pg.id not in emitted_goals:
                            emitted_goals.add(pg.id)
                            pg_pos = positions.get(pg.id, (0.0, 0.5))
                            pg_color = expr_color(pg.conclusion.identity_hash)
                            pg_spec = goal_visual_spec(pg, pg_color, style=style)
                            pg_label = _safe_label(pg_spec.label or pg.id)
                            pg_vname = _node_var(pg.id)
                            buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                            buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                            buf.write(f'{ind}self.play(ReplacementTransform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.9)\n')
                            buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                            buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
                else:
                    buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "split":
            # cases/rcases: goal splits into two sub-goals
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.5)\n')
                buf.write(f'{ind}self.play(active_nodes["{active_pre_goal_id}"].animate.shift(LEFT*0.5), run_time=0.4)\n')
                # Fade out the pre-goal
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.4)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
            # Post goals fan out
            n_post = len(step.post_goals)
            for i, pg in enumerate(step.post_goals):
                if pg.id not in emitted_goals:
                    emitted_goals.add(pg.id)
                    pg_pos = positions.get(pg.id, (-2.0 + i * 4.0, -1.0))
                    pg_color = expr_color(pg.conclusion.identity_hash)
                    pg_spec = goal_visual_spec(pg, pg_color, style=style)
                    pg_label = _safe_label(pg_spec.label or pg.id)
                    pg_vname = _node_var(pg.id)
                    buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                    buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                    buf.write(f'{ind}self.play(FadeIn({pg_vname}, shift=DOWN*0.3), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')

        elif anim == "spiral":
            # induction: base case + inductive step arc
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.5)\n')
                buf.write(f'{ind}self.play(Indicate(active_nodes["{active_pre_goal_id}"], scale_factor=1.1, color=YELLOW), run_time=0.5)\n')
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.4)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
            # Base + inductive step appear
            n_post = len(step.post_goals)
            for i, pg in enumerate(step.post_goals):
                if pg.id not in emitted_goals:
                    emitted_goals.add(pg.id)
                    angle = math.pi * i / max(n_post - 1, 1) if n_post > 1 else 0
                    spiral_x = 2.5 * math.cos(angle + math.pi / 2)
                    spiral_y = 1.5 * math.sin(angle + math.pi / 2)
                    pg_pos = positions.get(pg.id, (spiral_x, spiral_y))
                    pg_color = expr_color(pg.conclusion.identity_hash)
                    pg_spec = goal_visual_spec(pg, pg_color, style=style)
                    pg_label = _safe_label(pg_spec.label or pg.id)
                    pg_vname = _node_var(pg.id)
                    buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                    buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                    buf.write(f'{ind}self.play(GrowFromCenter({pg_vname}), run_time=0.6)\n')
                    buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')

        elif anim == "fan_out":
            # constructor: goal splits into sub-goal boxes side by side
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.4)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
            n_post = len(step.post_goals)
            for i, pg in enumerate(step.post_goals):
                if pg.id not in emitted_goals:
                    emitted_goals.add(pg.id)
                    offset = (i - (n_post - 1) / 2) * 3.5
                    pg_pos = positions.get(pg.id, (offset, 0.0))
                    pg_color = expr_color(pg.conclusion.identity_hash)
                    pg_spec = goal_visual_spec(pg, pg_color, style=style)
                    pg_label = _safe_label(pg_spec.label or pg.id)
                    pg_vname = _node_var(pg.id)
                    buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                    buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                    buf.write(f'{ind}self.play(FadeIn({pg_vname}, shift=RIGHT*0.3), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')

        elif anim == "witness_snap":
            # use: witness materializes inside exists container
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                witness = step.tactic_args[0] if step.tactic_args else "w"
                wit_color = var_color(witness)
                buf.write(f'{ind}_witness_dot = Dot(color="{wit_color}", radius=0.2).move_to(active_nodes["{active_pre_goal_id}"].get_center())\n')
                buf.write(f'{ind}self.play(GrowFromCenter(_witness_dot), run_time=0.5)\n')
                buf.write(f'{ind}self.play(FadeOut(_witness_dot), run_time=0.3)\n')
                for pg in step.post_goals:
                    if pg.id not in emitted_goals:
                        emitted_goals.add(pg.id)
                        pg_pos = positions.get(pg.id, (0.0, 0.5))
                        pg_color = expr_color(pg.conclusion.identity_hash)
                        pg_spec = goal_visual_spec(pg, pg_color, style=style)
                        pg_label = _safe_label(pg_spec.label or pg.id)
                        pg_vname = _node_var(pg.id)
                        buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                        buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                        buf.write(f'{ind}self.play(ReplacementTransform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.7)\n')
                        buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                        buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
                if not step.post_goals:
                    buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "bridge_chain":
            # calc: equality chain grows left to right
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                buf.write(f'{ind}self.play(Indicate(active_nodes["{active_pre_goal_id}"], scale_factor=1.15), run_time=0.5)\n')
                for pg in step.post_goals:
                    if pg.id not in emitted_goals:
                        emitted_goals.add(pg.id)
                        pg_pos = positions.get(pg.id, (0.0, -1.5))
                        pg_color = expr_color(pg.conclusion.identity_hash)
                        pg_spec = goal_visual_spec(pg, pg_color, style=style)
                        pg_label = _safe_label(pg_spec.label or pg.id)
                        pg_vname = _node_var(pg.id)
                        buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                        buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                        buf.write(f'{ind}self.play(Transform(active_nodes["{active_pre_goal_id}"], {pg_vname}), run_time=0.9)\n')
                        buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                        buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
                if not step.post_goals:
                    buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.5)\n')
                    buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    buf.write(f'{ind}self.wait(0.4)\n')

        elif anim == "contradiction":
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
                buf.write(f'{ind}self.play(Flash(active_nodes["{active_pre_goal_id}"], color=RED, flash_radius=0.8), run_time=0.5)\n')
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.4)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                buf.write(f'{ind}self.wait(0.4)\n')

        else:
            # Generic: show post goals
            if active_pre_goal_id:
                pre_pos = positions.get(active_pre_goal_id, (0.0, 0.0))
                buf.write(f'{ind}self.play(self.camera.frame.animate.move_to({_pos_str(pre_pos)}).set(width={cam_width}), run_time=0.4)\n')
            for pg in step.post_goals:
                if pg.id not in emitted_goals:
                    emitted_goals.add(pg.id)
                    pg_pos = positions.get(pg.id, (0.0, 0.0))
                    pg_color = expr_color(pg.conclusion.identity_hash)
                    pg_spec = goal_visual_spec(pg, pg_color, style=style)
                    pg_label = _safe_label(pg_spec.label or pg.id)
                    pg_vname = _node_var(pg.id)
                    buf.write(f'{ind}{pg_vname} = ProofNode("{pg_label}", "{pg_spec.encoding}", "{pg_color}")\n')
                    buf.write(f'{ind}{pg_vname}.move_to({_pos_str(pg_pos)})\n')
                    if active_pre_goal_id:
                        buf.write(f'{ind}self.play(Transform(active_nodes.get("{active_pre_goal_id}", {pg_vname}), {pg_vname}), run_time=0.7)\n')
                        buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                    else:
                        buf.write(f'{ind}self.play(FadeIn({pg_vname}), run_time=0.6)\n')
                    buf.write(f'{ind}active_nodes["{pg.id}"] = {pg_vname}\n')
            if not step.post_goals and active_pre_goal_id:
                buf.write(f'{ind}self.play(FadeOut(active_nodes["{active_pre_goal_id}"]), run_time=0.5)\n')
                buf.write(f'{ind}active_nodes.pop("{active_pre_goal_id}", None)\n')
                buf.write(f'{ind}self.wait(0.4)\n')

        buf.write(f'\n')

        # Every 10 steps: recap breath
        if step_count % RECAP_FREQUENCY == 0:
            buf.write(f'{ind}# ── Recap breath (step {step_count}) ──\n')
            buf.write(f'{ind}self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=14), run_time=0.5)\n')
            buf.write(f'{ind}self.wait(0.3)\n')
            buf.write(f'{ind}self.play(self.camera.frame.animate.set(width=8), run_time=0.4)\n')
            buf.write(f'\n')

    # ── 5. QED finale ─────────────────────────────────────────────────────────
    buf.write(f'{ind}# ── QED finale ──\n')
    buf.write(f'{ind}qed = Text("QED", font_size=72, color=ManimColor("#83C167"))\n')
    buf.write(f'{ind}self.play(\n')
    buf.write(f'{ind}    self.camera.frame.animate.set(width=16).move_to(ORIGIN),\n')
    buf.write(f'{ind}    run_time=2.0\n')
    buf.write(f'{ind})\n')
    buf.write(f'{ind}self.play(Write(qed), run_time=1.5)\n')
    buf.write(f'{ind}self.wait(1.5)\n')

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
