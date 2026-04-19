# lean2manim

**Lean 4 proof → deterministic Manim visualization**

`lean2manim` takes a Lean 4 proof trace (JSON produced by `ProofExtractor.lean`) and generates a fully animated Manim video that walks through each tactic step.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Convert proof JSON to video
lean2manim examples/nat_add.json -o nat_add.mp4

# Only generate the scene .py file (don't render)
lean2manim examples/nat_add.json --scene-only

# High quality render
lean2manim examples/nat_add.json -q high -o nat_add_hq.mp4
```

## Extracting a proof from Lean 4

`ProofExtractor.lean` contains a Lean 4 metaprogram that hooks into
`Lean.Elab.Tactic` to intercept tactic evaluation and serialize the proof state
to JSON. **Full automatic extraction requires lake integration** — the
`recordStep` hook must be wired into each tactic elaboration inside a lake build.

The `#extract_proof` command, when used standalone, writes a *skeleton* JSON
trace to the configured output path (see `set_option lean2manim.output`) and
logs setup instructions. The hand-written JSON traces in `examples/` show the
full expected format and can be used directly with `lean2manim`.

```lean
-- In a lake project, import ProofExtractor and wrap your proof:
import Lean2Manim.ProofExtractor

set_option lean2manim.output "my_proof.json" in
#extract_proof
theorem my_thm : ∀ n : ℕ, n + 0 = n := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.succ_add, ih]
```

Until full lake integration is available, write or generate proof traces in the
[JSON format](examples/nat_add.json) and feed them directly to `lean2manim`.

## Architecture

```
ProofExtractor.lean  ──►  proof.json  ──►  parser.py  ──►  ProofTree
                                                                │
                                                         visual_dispatch.py
                                                                │
                                                           layout.py  (ForceLayout)
                                                                │
                                                         scene_graph.py
                                                                │
                                                          emitter.py  ──►  scene.py  ──►  manim render  ──►  video.mp4
```

## Visual encodings

| Type category | Visual encoding |
|--------------|-----------------|
| Nat / Int    | Number line     |
| Real         | Axis region     |
| Prop         | Generic box     |
| Set          | Venn diagram    |
| List         | Square array    |
| Function     | Arrow blob      |
| Eq           | Bridge          |
| And          | Conjoined boxes |
| Or           | Split boxes     |
| Forall       | Slider          |
| Exists       | Container       |

## Running tests

```bash
cd lean2manim && python -m pytest tests/ -v
```
