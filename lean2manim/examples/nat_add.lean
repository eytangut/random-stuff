-- Example: ∀ n : ℕ, n + 0 = n (via induction)
-- The hand-written proof trace for this theorem is in nat_add.json and can be
-- fed directly to lean2manim:
--
--   lean2manim examples/nat_add.json -o nat_add.mp4
--
-- Full tactic-level extraction via #extract_proof requires lake integration;
-- see lean2manim/README.md for details.

-- set_option lean2manim.output "nat_add.json" in
-- #extract_proof
theorem nat_add_zero : ∀ n : ℕ, n + 0 = n := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.succ_add, ih]
