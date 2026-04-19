from __future__ import annotations
import math
from typing import Any


class Node:
    def __init__(self, node_id: str, x: float = 0.0, y: float = 0.0):
        self.id = node_id
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0


class Edge:
    def __init__(self, src: str, dst: str):
        self.src = src
        self.dst = dst


class ForceLayout:
    """Deterministic spring-repulsion layout.

    Uses a fixed seed derived from the proof hash so same input → same layout.
    """

    REPULSION = 1200.0
    SPRING_K  = 0.08
    SPRING_L  = 2.5      # rest length
    DAMPING   = 0.82
    ITERATIONS = 200

    def __init__(self, proof_hash: str):
        # deterministic PRNG — LCG seeded by proof_hash
        # Use hashlib to handle any string, not just hex
        import hashlib
        seed = int(hashlib.md5(proof_hash.encode()).hexdigest()[:8], 16)
        self._rng_state = seed

    def _rand(self) -> float:
        """LCG pseudo-random in [0, 1)."""
        self._rng_state = (self._rng_state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._rng_state / 0xFFFFFFFF

    def initial_positions(self, node_ids: list[str]) -> dict[str, tuple[float, float]]:
        """Place nodes in a circle with slight jitter."""
        n = len(node_ids)
        positions = {}
        for i, nid in enumerate(node_ids):
            angle = 2 * math.pi * i / max(n, 1)
            r = 2.5 + self._rand() * 0.5
            positions[nid] = (r * math.cos(angle), r * math.sin(angle))
        return positions

    def run(
        self,
        node_ids: list[str],
        edges: list[tuple[str, str]],
        fixed: dict[str, tuple[float, float]] | None = None,
    ) -> dict[str, tuple[float, float]]:
        """Return converged (x, y) for all nodes."""
        if not node_ids:
            return {}

        nodes: dict[str, Node] = {}
        init = self.initial_positions(node_ids)
        for nid in node_ids:
            x, y = init[nid]
            if fixed and nid in fixed:
                x, y = fixed[nid]
            nodes[nid] = Node(nid, x, y)

        edge_pairs = [(e[0], e[1]) for e in edges if e[0] in nodes and e[1] in nodes]

        for _ in range(self.ITERATIONS):
            # Reset forces
            for n in nodes.values():
                n.vx *= self.DAMPING
                n.vy *= self.DAMPING

            # Repulsion (all pairs)
            node_list = list(nodes.values())
            for i in range(len(node_list)):
                for j in range(i + 1, len(node_list)):
                    a, b = node_list[i], node_list[j]
                    dx = a.x - b.x
                    dy = a.y - b.y
                    dist2 = dx * dx + dy * dy + 0.01
                    dist = math.sqrt(dist2)
                    force = self.REPULSION / dist2
                    fx = force * dx / dist
                    fy = force * dy / dist
                    a.vx += fx; a.vy += fy
                    b.vx -= fx; b.vy -= fy

            # Spring attraction (edges)
            for src_id, dst_id in edge_pairs:
                a, b = nodes[src_id], nodes[dst_id]
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                force = self.SPRING_K * (dist - self.SPRING_L)
                fx = force * dx / dist
                fy = force * dy / dist
                a.vx += fx; a.vy += fy
                b.vx -= fx; b.vy -= fy

            # Integrate
            for n in nodes.values():
                if fixed and n.id in fixed:
                    n.x, n.y = fixed[n.id]
                else:
                    n.x += n.vx
                    n.y += n.vy

        return {nid: (n.x, n.y) for nid, n in nodes.items()}
