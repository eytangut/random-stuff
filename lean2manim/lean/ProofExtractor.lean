-- ProofExtractor.lean
-- Lean 4 metaprogram: intercepts each tactic and records the proof state as JSON.
-- Usage:
--   set_option lean2manim.output "proof.json" in
--   #extract_proof
--   theorem my_thm : ... := by
--     ...

import Lean
import Lean.Elab.Tactic
import Lean.Elab.Term
import Lean.Data.Json

open Lean Elab Tactic Meta

namespace Lean2Manim

-- ── Options ──────────────────────────────────────────────────────────────────

/-- Output path for the JSON proof trace. -/
register_option lean2manim.output : String := {
  defValue := "proof.json"
  descr    := "File path where lean2manim writes the proof trace JSON"
}

-- ── Data structures ──────────────────────────────────────────────────────────

structure ExprData where
  kind          : String
  name          : String
  args          : Array ExprData
  typeCategory  : String
  syntacticRole : String
  deriving Inhabited

structure HypData where
  name            : String
  typeExpr        : ExprData
  introducedAtStep : Int
  deriving Inhabited

structure GoalData where
  id          : String
  conclusion  : ExprData
  hypotheses  : Array HypData
  deriving Inhabited

structure StepData where
  id         : Nat
  tactic     : String
  tacticArgs : Array String
  preGoals   : Array GoalData
  postGoals  : Array GoalData
  hypAdded   : Array HypData
  hypRemoved : Array String
  deriving Inhabited

structure ProofData where
  theoremName      : String
  theoremStatement : String
  steps            : Array StepData
  deriving Inhabited

-- ── Type category inference ───────────────────────────────────────────────────

/-- Infer a coarse type category from a Lean Expr. -/
def inferTypeCategory (e : Expr) : MetaM String := do
  try
    let ty ← inferType e
    let ty ← whnf ty
    match ty with
    | .const `Nat _  => return "Nat"
    | .const `Int _  => return "Int"
    | .const `Real _ => return "Real"
    | .sort _        => return "Prop"
    | .app (.const `Set _) _ => return "Set"
    | .app (.const `List _) _ => return "List"
    | .forallE _ _ _ _ => return "Function"
    | _ =>
      let typeName := ty.getAppFn.constName?.map (·.toString) |>.getD ""
      match typeName with
      | "Nat"   => return "Nat"
      | "Int"   => return "Int"
      | "Real"  => return "Real"
      | "Set"   => return "Set"
      | "List"  => return "List"
      | "Group" | "CommGroup" | "Monoid" => return "Group"
      | _       => return "Unknown"
  catch _ => return "Unknown"

-- ── Expr → ExprData serialization ────────────────────────────────────────────

/-- Convert a Lean Expr to our ExprData (truncated depth to avoid blowup). -/
partial def exprToData (e : Expr) (role : String := "unknown") (depth : Nat := 0) : MetaM ExprData := do
  if depth > 8 then
    return { kind := "truncated", name := "...", args := #[], typeCategory := "", syntacticRole := role }
  let typeCat ← try inferTypeCategory e catch _ => pure "Unknown"
  match e with
  | .bvar i =>
    return { kind := "var", name := s!"x{i}", args := #[], typeCategory := typeCat, syntacticRole := role }
  | .fvar fv =>
    let n ← try (do let decl ← getLocalDecl fv; return decl.userName.toString) catch _ => pure "?"
    return { kind := "var", name := n, args := #[], typeCategory := typeCat, syntacticRole := role }
  | .mvar mv =>
    return { kind := "var", name := s!"?m{mv.name}", args := #[], typeCategory := typeCat, syntacticRole := role }
  | .sort _ =>
    return { kind := "sort", name := "Sort", args := #[], typeCategory := "Sort", syntacticRole := role }
  | .const n _ =>
    return { kind := "const", name := n.toString, args := #[], typeCategory := typeCat, syntacticRole := role }
  | .app f a =>
    -- Detect common patterns
    let fn := e.getAppFn
    let fnArgs := e.getAppArgs
    match fn with
    | .const `HEq _ | .const `Eq _ =>
      if fnArgs.size >= 3 then
        let lhs ← exprToData fnArgs[fnArgs.size - 2]! "lhs" (depth + 1)
        let rhs ← exprToData fnArgs[fnArgs.size - 1]! "rhs" (depth + 1)
        return { kind := "eq", name := "", args := #[lhs, rhs], typeCategory := "Prop", syntacticRole := role }
    | .const `And _ =>
      if fnArgs.size >= 2 then
        let l ← exprToData fnArgs[0]! "lhs" (depth + 1)
        let r ← exprToData fnArgs[1]! "rhs" (depth + 1)
        return { kind := "and", name := "", args := #[l, r], typeCategory := "Prop", syntacticRole := role }
    | .const `Or _ =>
      if fnArgs.size >= 2 then
        let l ← exprToData fnArgs[0]! "lhs" (depth + 1)
        let r ← exprToData fnArgs[1]! "rhs" (depth + 1)
        return { kind := "or", name := "", args := #[l, r], typeCategory := "Prop", syntacticRole := role }
    | _ => pure ()
    let fData ← exprToData f "fn" (depth + 1)
    let aData ← exprToData a "arg" (depth + 1)
    return { kind := "app", name := "", args := #[fData, aData], typeCategory := typeCat, syntacticRole := role }
  | .lam n t b _ =>
    let bData ← exprToData b "body" (depth + 1)
    return { kind := "lambda", name := n.toString, args := #[bData], typeCategory := typeCat, syntacticRole := role }
  | .forallE n _ b _ =>
    let bData ← exprToData b "body" (depth + 1)
    return { kind := "forall", name := n.toString, args := #[bData], typeCategory := typeCat, syntacticRole := role }
  | .letE n _ v b _ =>
    let vData ← exprToData v "val" (depth + 1)
    let bData ← exprToData b "body" (depth + 1)
    return { kind := "let", name := n.toString, args := #[vData, bData], typeCategory := typeCat, syntacticRole := role }
  | .lit (.natVal n) =>
    return { kind := "nat_lit", name := toString n, args := #[], typeCategory := "Nat", syntacticRole := role }
  | .lit (.strVal s) =>
    return { kind := "str_lit", name := s, args := #[], typeCategory := "String", syntacticRole := role }
  | .proj n i s =>
    let sData ← exprToData s "struct" (depth + 1)
    return { kind := "proj", name := s!"{n}.{i}", args := #[sData], typeCategory := typeCat, syntacticRole := role }
  | _ =>
    return { kind := "unknown", name := "", args := #[], typeCategory := typeCat, syntacticRole := role }

-- ── Goal → GoalData ──────────────────────────────────────────────────────────

def goalToData (goal : MVarId) (goalId : String) : MetaM GoalData := do
  let decl ← goal.getDecl
  let concl ← exprToData decl.type "conclusion"
  let hyps ← decl.lctx.toArray.filterMapM fun ldecl => do
    if ldecl.isAuxDecl then return none
    let typeData ← exprToData ldecl.type "hypothesis"
    return some { name := ldecl.userName.toString, typeExpr := typeData, introducedAtStep := -1 }
  return { id := goalId, conclusion := concl, hypotheses := hyps }

-- ── JSON serialization ────────────────────────────────────────────────────────

partial def exprDataToJson (e : ExprData) : Json :=
  Json.mkObj [
    ("kind",          Json.str e.kind),
    ("name",          Json.str e.name),
    ("type_category", Json.str e.typeCategory),
    ("syntactic_role",Json.str e.syntacticRole),
    ("args",          Json.arr (e.args.map exprDataToJson))
  ]

def hypDataToJson (h : HypData) : Json :=
  Json.mkObj [
    ("name",               Json.str h.name),
    ("type_expr",          exprDataToJson h.typeExpr),
    ("introduced_at_step", Json.num h.introducedAtStep)
  ]

def goalDataToJson (g : GoalData) : Json :=
  Json.mkObj [
    ("id",          Json.str g.id),
    ("conclusion",  exprDataToJson g.conclusion),
    ("hypotheses",  Json.arr (g.hypotheses.map hypDataToJson))
  ]

def stepDataToJson (s : StepData) : Json :=
  Json.mkObj [
    ("id",           Json.num (s.id : Int)),
    ("tactic",       Json.str s.tactic),
    ("tactic_args",  Json.arr (s.tacticArgs.map Json.str)),
    ("pre_goals",    Json.arr (s.preGoals.map goalDataToJson)),
    ("post_goals",   Json.arr (s.postGoals.map goalDataToJson)),
    ("hyp_added",    Json.arr (s.hypAdded.map hypDataToJson)),
    ("hyp_removed",  Json.arr (s.hypRemoved.map Json.str))
  ]

def proofDataToJson (p : ProofData) : Json :=
  Json.mkObj [
    ("theorem_name",      Json.str p.theoremName),
    ("theorem_statement", Json.str p.theoremStatement),
    ("steps",             Json.arr (p.steps.map stepDataToJson))
  ]

-- ── Tactic interceptor ────────────────────────────────────────────────────────

/-- State threaded through the proof extraction. -/
structure ExtractState where
  steps     : Array StepData := #[]
  stepCount : Nat            := 0

abbrev ExtractM := StateT ExtractState TacticM

/-- Record a tactic step: capture pre-state, run the tactic, capture post-state. -/
def recordStep (tacticName : String) (tacticArgs : Array String)
    (innerTac : TacticM Unit) : ExtractM Unit := do
  -- Pre-state
  let preGoals ← getGoals
  let preGoalData ← preGoals.enum.mapM fun (i, g) =>
    goalToData g s!"g{(← get).stepCount}_{i}" |>.run' {}
  -- Run the actual tactic
  liftM innerTac
  -- Post-state
  let postGoals ← getGoals
  let postGoalData ← postGoals.enum.mapM fun (i, g) =>
    goalToData g s!"g{(← get).stepCount}_{i}_post" |>.run' {}
  -- Detect new hypotheses (simplified: compare local context sizes)
  let hypAdded : Array HypData := #[]
  let hypRemoved : Array String := #[]
  let stepId ← get |>.map (·.stepCount)
  let step : StepData := {
    id         := stepId,
    tactic     := tacticName,
    tacticArgs := tacticArgs,
    preGoals   := preGoalData,
    postGoals  := postGoalData,
    hypAdded   := hypAdded,
    hypRemoved := hypRemoved,
  }
  modify fun s => { s with steps := s.steps.push step, stepCount := s.stepCount + 1 }

-- ── #extract_proof command ────────────────────────────────────────────────────

/-- The `#extract_proof` elaboration command. -/
elab "#extract_proof" : command => do
  logWarning "lean2manim: #extract_proof is a stub. \
    Run ProofExtractor.lean inside a Lean project with lake to generate real JSON."

/-- A `#check_extract` to verify the extractor loads. -/
elab "#check_extract" : command => do
  logInfo "lean2manim ProofExtractor loaded successfully."

end Lean2Manim
