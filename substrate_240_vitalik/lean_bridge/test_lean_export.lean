import Mathlib

/--
Teorema de exemplo: A função identidade é sua própria inversa.
Este teorema simples demonstra a estrutura básica de um teorema Lean 4
que será convertido pela Lean Bridge para o formato BEAVER.
-/
theorem identity_self_inverse (f : α → α) (h : f = id) : f ∘ f = id := by
  rw [h]
  simp

/--
Teorema: O total de supply de um token ERC-20 é preservado
após uma transferência válida.
-/
theorem erc20_transfer_preserves_total_supply
    (ledger : Ledger) (from to : Address) (amount : ℕ)
    (h_valid : valid_erc20_transfer ledger from to amount) :
    total_supply ledger = total_supply (execute_transfer ledger from to amount) := by
  rcases h_valid with ⟨h_balance, h_allowance⟩
  rw [execute_transfer_def]
  simp [total_supply_def, h_balance, h_allowance]
  ring
