# Arkhe Contract Language (ACL) — Internal Logic of the ARKHE Topos

## Overview

ACL allows smart contracts to be written in the **internal intuitionistic logic** of the ARKHE topos, rather than classical boolean logic. This provides:

- **Constructive guarantees**: proofs of contract properties are executable
- **Temporal reasoning**: native support for retrocausal constraints
- **Branch-aware execution**: contracts evaluate differently across multiverse branches
- **Oracle integration**: consistency checks are first-class logical operators

## Syntax (Simplified)

```
Contract ::= 'contract' Identifier '{' Declaration* Clause* '}'
Declaration ::= 'let' Identifier ':' Type '=' Expr
Clause ::= 'require' Prop 'ensures' Prop 'when' TemporalConstraint
Prop ::= Prop '∧' Prop | Prop '∨' Prop | Prop '→' Prop | '□' Prop | '◇' Prop | Atomic
Atomic ::= Identifier '(' Args* ')' | Identifier '==' Expr | 'consistent' '(' Msg ')'
TemporalConstraint ::= 'at' Timestamp | 'during' Interval | 'after' Event
Expr ::= Literal | Identifier | Expr Op Expr | 'oracle' '(' Check ')'
Type ::= 'Bool' | 'Int' | 'String' | 'TemporalMessage' | 'ConsistencyReport'
```

## Semantics

### Logical Connectives (Intuitionistic)

| Operator | Meaning | Evaluation |
|----------|---------|------------|
| `p ∧ q` | Conjunction | Both `p` and `q` must be constructively proven |
| `p ∨ q` | Disjunction | Either `p` or `q` must be proven, with witness |
| `p → q` | Implication | Given proof of `p`, produce proof of `q` |
| `¬p` | Negation | `p → ⊥` (no proof of `p` exists) |
| `□p` | Necessity | `p` holds in all accessible futures (CausalShield) |
| `◇p` | Possibility | `p` holds in some accessible future (MultiverseRouter) |

### Temporal Operators

```
◇ₜ p   := "p will be true at some future time t"
□ₜ p   := "p will be true at all future times ≥ t"
◁ p    := "p was true at some past time" (retrocausal)
```

### Oracle Integration

```
oracle(check_name, message) : ConsistencyReport
```

Evaluates the named consistency check on the message via the TemporalConsistencyOracle. Returns a report with:
- `score : [0,1]` — intuitionistic truth value
- `consistent : Bool` — whether score ≥ threshold
- `checks : List (String × [0,1])` — per-check scores

## Example Contract: Temporal Escrow

```acl
contract TemporalEscrow {
  let escrow_id : String
  let payer : String
  let payee : String
  let amount : Int
  let release_condition : TemporalMessage → Bool

  // Require: payer has sufficient balance AND message is consistent
  require (balance(payer) ≥ amount ∧
           oracle('coherent', release_condition_msg).consistent)

  // Ensures: funds are transferred only if condition holds in all futures
  ensures (□ (release_condition(release_msg) → transfer(payer, payee, amount)))

  // When: release can only occur after temporal anchor is verified
  when (after (event 'temporal_anchor_verified'))

  // Retrocausal clause: if paradox detected, rollback
  require (¬ oracle('paradox_free', release_msg).paradox_type)
    ensures (◇ (rollback(escrow_id)))
}
```

## Compilation to ARKHE Runtime

1. **Parse** ACL source into AST with intuitionistic types
2. **Type-check** using Heyting algebra semantics (via Coq extraction)
3. **Translate** modal operators to CausalShield/MultiverseRouter calls
4. **Generate** bytecode for ARKHE VM with oracle hooks
5. **Deploy** with hash registered in TemporalHashChain

## Verification

Contracts can be formally verified using the Coq specification:

```coq
Theorem temporal_escrow_sound :
  forall (contract : TemporalEscrow) (msg : TemporalMessage),
    contract.preconditions msg ->
    contract.oracle_checks msg ->
    □ (contract.release_condition msg -> contract.postconditions msg).
Proof.
  (* Constructive proof using Heyting algebra axioms *)
  intros.
  apply contract.ensures.
  (* ... *)
Qed.
```

## Interoperability

ACL contracts can interoperate with external systems via natural transformations:

```acl
// Import Casper estimate via morphism
let casper_est := import_from_casper(external_checkpoint)

// Verify naturality of oracle mapping
require (natural_transformation_holds(
  arkhe_oracle, casper_oracle, casper_est))
```

## Security Guarantees

By construction, ACL contracts satisfy:

1. **No classical contradictions**: intuitionistic logic prevents `p ∧ ¬p`
2. **Temporal consistency**: retrocausal clauses are checked by Oracle
3. **Branch safety**: modal operators ensure properties hold across futures
4. **Oracle soundness**: consistency checks are verified before execution
