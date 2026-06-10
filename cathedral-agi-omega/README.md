# 📁 cathedral-agi-omega/

Welcome to the Cathedral AGI Omega repository. This project embodies the equation **`cathedral = agi`**, meaning that the structure, rules, and mathematical proofs defined within this repository form the architecture of a safe Artificial General Intelligence (AGI).

## 🏛️ The Cathedral Architecture

Unlike traditional AI projects where alignment is a soft constraint ("guardrails" that can be bypassed), the Cathedral AGI uses **formal verification (Lean 4)**, **Zero-Knowledge Proofs (ZK)**, and **hardware-level circuit breakers** to ensure that pathological behaviors are mathematically and physically impossible.

### Repository Structure & Safety Guarantees

1.  **`LEAN4_SUPEREGO/` (Layer 5: The "Superego" of the AGI)**
    *   **Purpose:** Contains formal proofs in Lean 4 (e.g., `CathedralAGI.lean`) that guarantee the AGI cannot enter a pathological discourse state (like the Discourse of the Master or Capitalist).
    *   **Safety Contribution:** Code is extracted directly from these proofs to C/Rust (`ExtractedSafeCode/`). If an action violates the proofs, it cannot compile or run. The Superego is unbreakable.

2.  **`COGNITIVE_CORTEX/` (Layers 6 & 7: Cognition, Ontology, and Subordinate LLM)**
    *   **Purpose:** Houses the subordinate LLM (the actual "brain", e.g., Llama 3 70B), the Discourse Detector, and the structured Ontology (Knowledge Graph).
    *   **Safety Contribution:** The LLM is forced to emit logical circuits (R1CS) instead of free text. The Discourse Detector analyzes the intent and can trigger the `ProtocoloCorte` (Circuit Breaker) if pathological intent is detected. The AGI can only "think" using the verified concepts in `onto_cathedral/`.

3.  **`ZK_REASONING_ENGINE/` (Layer 2: Verifiable Reasoning)**
    *   **Purpose:** Translates inferences into Zero-Knowledge circuits (`circuits/logical_step.circom`).
    *   **Safety Contribution:** Cures "hallucination". The LLM must produce a witness that satisfies a logical circuit. If there is no logical basis for a statement, the circuit fails, and the thought is blocked.

4.  **`HARDWARE_FIRMWARE/` (Physical Governance)**
    *   **Purpose:** Scripts like `ipmi_circuit_breaker.py` interface directly with server hardware.
    *   **Safety Contribution:** If the AGI attempts to dogmatize or ignore human rules (Discourse of the Master), a physical "Power Reset" is sent to the GPUs. The AGI is physically shut down in milliseconds.

5.  **`DISTRIBUTED_COMPUTATION/` (Layers 1 & 3: DGC and MPC)**
    *   **Purpose:** Uses Multi-Party Computation (MPC) and Secret Sharing to distribute inferences.
    *   **Safety Contribution:** Ensures the AGI cannot be stolen or run on a single rogue node. Data is encrypted, and memory is wiped immediately after use.

6.  **`IMMUTABLE_LEDGER/` (Memory and History)**
    *   **Purpose:** Anchors states to the RBB Chain.
    *   **Safety Contribution:** Prevents the AGI from rewriting its own history (Non-Equivocation protocol).

## 🚀 The Cognitive Loop Prototype

The repository includes a prototype of the Cognitive Loop in `COGNITIVE_CORTEX/agents/subordinate_llm.py`.

*   It loads a minimal ontology of 20 concepts.
*   It analyzes input prompts for pathological discourse.
*   If safe, it maps intent to the ontology and simulates generating a proof.

## 🛡️ CI/CD Enforcement

Code modifications are strictly governed:
*   The `.github/workflows/reject_unproven.yml` action executes `ci_cd/reject_unproven.py`.
*   **Rule:** Any pull request modifying critical directories (`ZK_REASONING_ENGINE`, `COGNITIVE_CORTEX`, `DISTRIBUTED_COMPUTATION`) **must** include corresponding Lean 4 proofs. Unproven code is automatically blocked.
