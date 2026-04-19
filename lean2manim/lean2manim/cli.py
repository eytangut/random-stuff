import argparse
import subprocess
import sys
from pathlib import Path

from .parser import load_proof_tree
from .emitter import emit_scene_file


def main():
    parser = argparse.ArgumentParser(
        prog="lean2manim",
        description="Convert a Lean 4 proof (JSON) into a Manim visualization video.",
    )
    parser.add_argument("proof_json", help="Path to the proof JSON file (from ProofExtractor.lean)")
    parser.add_argument("--output", "-o", default="video.mp4", help="Output video file (default: video.mp4)")
    parser.add_argument(
        "--quality", "-q", choices=["low", "medium", "high"], default="medium",
        help="Render quality (default: medium)"
    )
    parser.add_argument(
        "--style", "-s", choices=["geometric", "algebraic", "auto"], default="auto",
        help=(
            "Visual style for proof objects. "
            "'auto' (default): type-based dispatch (number lines for Nat, Venn for Set, …). "
            "'geometric': always prefer spatial/visual representations (number lines, Venn diagrams). "
            "'algebraic': prefer symbolic box representations with equation bridges."
        ),
    )
    parser.add_argument("--scene-only", action="store_true", help="Only write the scene .py file, do not render")
    args = parser.parse_args()

    proof_path = Path(args.proof_json)
    if not proof_path.exists():
        print(f"Error: proof JSON not found: {proof_path}", file=sys.stderr)
        sys.exit(1)

    proof_tree = load_proof_tree(proof_path)
    scene_path = proof_path.with_suffix(".scene.py")

    print(f"[lean2manim] Loaded proof: {proof_tree.theorem_name} ({len(proof_tree.steps)} steps)")
    emit_scene_file(proof_tree, str(scene_path), style=args.style)
    print(f"[lean2manim] Scene written to: {scene_path}")

    if args.scene_only:
        return

    quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}[args.quality]
    output_path = Path(args.output)
    cmd = [
        sys.executable, "-m", "manim", "render",
        quality_flag, str(scene_path), "ProofScene",
        "--output_file", str(output_path),
    ]
    print(f"[lean2manim] Rendering: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[lean2manim] Render failed.", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"[lean2manim] Done: {output_path}")


if __name__ == "__main__":
    main()
