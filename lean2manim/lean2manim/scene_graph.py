from __future__ import annotations
from dataclasses import dataclass, field
from .proof_tree import GoalState, Hypothesis, TacticStep
from .colors import var_color, expr_color
from .visual_dispatch import goal_visual_spec, VisualSpec


@dataclass
class SceneNode:
    """A single visual object living in the persistent scene."""
    node_id: str
    label: str
    spec: VisualSpec
    position: tuple[float, float] = (0.0, 0.0)
    scale: float = 1.0
    opacity: float = 1.0
    on_shelf: bool = False
    closed: bool = False
    color: str = "#FFFFFF"
    step_introduced: int = 0
    connected_to: list[str] = field(default_factory=list)  # node_ids of tactic edges


class SceneGraph:
    """Tracks all proof objects, their visual state, and tactic connections."""

    def __init__(self, proof_hash: str):
        self.proof_hash = proof_hash
        self._nodes: dict[str, SceneNode] = {}
        self._tactic_edges: list[tuple[str, str, str]] = []  # (src, dst, label)
        self._step_count = 0

    # ── node management ──────────────────────────────────────────────────────

    def add_goal_node(self, goal: GoalState, step_id: int) -> SceneNode:
        color = expr_color(goal.conclusion.identity_hash)
        spec = goal_visual_spec(goal, color)
        label = spec.label or goal.id
        node = SceneNode(
            node_id=goal.id,
            label=label,
            spec=spec,
            color=color,
            step_introduced=step_id,
        )
        self._nodes[goal.id] = node
        return node

    def add_hyp_node(self, hyp: Hypothesis, step_id: int) -> SceneNode:
        color = var_color(hyp.name)
        from .visual_dispatch import _expr_encoding, _expr_label, VisualSpec
        spec = VisualSpec(
            encoding=_expr_encoding(hyp.type_expr),
            label=hyp.name,
            color=color,
            anim_hint="fly_in",
        )
        node = SceneNode(
            node_id=f"hyp_{hyp.name}_{step_id}",
            label=hyp.name,
            spec=spec,
            color=color,
            step_introduced=step_id,
        )
        self._nodes[node.node_id] = node
        return node

    def get_node(self, node_id: str) -> SceneNode | None:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[SceneNode]:
        return list(self._nodes.values())

    def active_nodes(self) -> list[SceneNode]:
        return [n for n in self._nodes.values() if not n.closed and not n.on_shelf]

    def shelf_nodes(self) -> list[SceneNode]:
        return [n for n in self._nodes.values() if n.on_shelf]

    def close_goal(self, goal_id: str) -> None:
        if goal_id in self._nodes:
            self._nodes[goal_id].closed = True

    def send_to_shelf(self, node_id: str) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].on_shelf = True
            self._nodes[node_id].scale = 0.4
            self._nodes[node_id].opacity = 0.6

    def recall_from_shelf(self, node_id: str) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].on_shelf = False
            self._nodes[node_id].scale = 1.0
            self._nodes[node_id].opacity = 1.0

    def add_tactic_edge(self, src_id: str, dst_id: str, label: str) -> None:
        self._tactic_edges.append((src_id, dst_id, label))
        if src_id in self._nodes:
            self._nodes[src_id].connected_to.append(dst_id)

    def edges(self) -> list[tuple[str, str, str]]:
        return list(self._tactic_edges)

    def node_edges(self) -> list[tuple[str, str]]:
        return [(s, d) for s, d, _ in self._tactic_edges]
