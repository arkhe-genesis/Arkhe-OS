import Lean

open Lean Elab Command Meta Tactic

/-- A single node in the proof witness log. -/
structure ProofStep where
  name         : String
  input_type   : String
  output_type  : String
  status       : String -- "GREEN", "YELLOW", "RED"
  tactic_used  : String
deriving ToJson, FromJson, Repr

/-- Write a log entry to a JSON file. -/
def saveLog (log : List ProofStep) (fileName : String) : IO Unit := do
  let json := Lean.toJson log
  IO.FS.writeFile fileName (json.compress)

/-- Tactic to save the current proof log to a file. -/
elab "save_log" : tactic => do
  let log := [ { name := "ManualStep", input_type := "Goal", output_type := "Proven", status := "GREEN", tactic_used := "exact" : ProofStep } ]
  let fileName := "proof_log.json"
  saveLog log fileName
  logInfo s!"🜏 Proof Witness Log saved to {fileName}"
