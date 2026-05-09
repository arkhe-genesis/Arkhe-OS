---
name: psa-pefm
description: Use for epistemic defense, measuring semantic coherence (PSA), and anticipating failure risk (PEFM). Includes the Diamond Pipeline for hallucination reduction.
---

# Epistemic Defense System (PSA/PEFM)

Deterministic instrumentation for measuring and predicting epistemic failures in AI-generated artifacts.

## Core Components

### 1. PSA (Predicted Safety Analysis)
Measures the structural and semantic coherence of an artifact using 6 key invariants (I1-I6).
- `psa_evaluate`: Calculates connectivity (S), consistency (C), triviality (I), predictability (P), and relevance (E).

### 2. PEFM (Predictive Epistemic Failure Model)
Anticipates the probability of failure based on enriched PSA features.
- `pefm_predict`: Returns `failure_probability` and risk levels (LOW, MEDIUM, HIGH).

### 3. Diamond Pipeline
A multi-stage process to minimize hallucinations:
1. **Diverge**: Generate multiple candidate artifacts.
2. **Filter**: Evaluate candidates using `psa_evaluate`.
3. **Converge**: Select the candidate with the highest structural integrity.

## Workflow

### Evaluating an Artifact
1. Extract claims and relations from the artifact.
2. Run `psa_evaluate` to get the Coherence Score.
3. Check the `hash` for auditability (I5).

### Predicting Failure
1. If the score is marginal, run `pefm_predict` using the same graph.
2. Review the `explanation` to understand feature contributions (I4).

### Generating Safe Content
Use `diamond_pipeline` with your initial prompt to get a structurally verified response.

## Invariants (I1-I6)
| ID | Invariant | Description |
|----|-----------|-------------|
| I1 | Non-Truth | Prediction is a probability, not absolute truth. |
| I2 | Monotonicity | Risk increases predictably with decoherence. |
| I3 | Causality | Temporal split enforcement for all predictions. |
| I4 | Transparency | Every score must have a feature-level explanation. |
| I5 | Auditability | Canonical hash (G) reproduces the score. |
| I6 | Relevance | Prioritize risk in critical domains (e.g., governance). |
