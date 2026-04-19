-- Example: ∀ n : ℕ, n + 0 = n (via induction)
set_option lean2manim.output "nat_add.json" in
#extract_proof
theorem nat_add_zero : ∀ n : ℕ, n + 0 = n := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.succ_add, ih]
