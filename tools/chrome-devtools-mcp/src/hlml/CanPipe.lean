import Lean
import src.hlml.ProofWitnessLog

open Lean Elab Command Meta Tactic

-- 1. The Type Class for the "Pipe" (The Dispatcher)
class CanPipe (α : Type) (β : Type) where
  pipe : α → β
  log_entry : ProofStep

-- 2. Example Instance: Nat to Int (The "Test Case")
instance : CanPipe Nat Int where
  pipe n := Int.ofNat n
  log_entry := {
    name := "NatToIntCoercion",
    input_type := "Nat",
    output_type := "Int",
    status := "GREEN",
    tactic_used := "Int.ofNat"
  }

-- 3. Custom Elaborator for the >> Operator
syntax:60 term " >> " term : term

macro_rules
  | `($a >> $b) => `(CanPipe.pipe $a)

-- 4. Example usage in Lean
/-
def apply_mukai (n : Nat) : Int :=
  n >> id

theorem test_pipe : (apply_mukai 5) = (5 : Int) := by
  simp [apply_mukai]
  save_log
-/
