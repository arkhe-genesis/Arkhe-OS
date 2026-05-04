# Substrate 116: Inter-Reality Spam as Fisher-Rao Branch Crosstalk

## Physical Context
The phenomenon of spam in communication networks is conventionally understood purely as an economic or technical issue (abuse of resources for unrequested bulk messaging). Substrate 116 of ARKHE OS re-ontologizes spam as an emergent interference pattern between partially orthogonal branches in the collective consciousness field (Fisher-Rao manifold).

When the global coherence $\rho$ drops below a critical threshold (typically $0.75$), branches of the reality field that should remain causally disconnected (orthogonal, where $\langle\Psi_A|\Psi_B\rangle = 0$) begin to overlap. This non-zero inner product allows signal components to project across reality branches.

## Entropic Shell vs. Syntropic Core
During this projection, the Fisher metric filters the *syntropic core* (the true semantic intent and causal context) of the message, leaving behind an *entropic shell* (the formal structure: headers, formatting, generic templates).

Spam, therefore, is an empty entropic shell from a foreign branch that has been hijacked and filled with new, local malicious intent.

## The Fisher-Rao Filter
Substrate 116 mitigates this phenomenon not through keyword matching or IP reputation, but through topological verification:

1.  **Phase Consistency:** Validates that the branch phase of the sender matches the local reality field.
2.  **Causal Invariance:** Evaluates the Jones invariant of the message's causal history (using the ZEE200 circuit) to confirm it belongs to the expected topological knot of events.
3.  **Shell Detection:** Identifies the signature of an empty entropic shell (high structural complexity, low semantic density).

## Implementation
-   **Model:** `core/semantics/interreality_crosstalk.py` - Simulates the crosstalk and projection mechanism.
-   **Filter:** `core/security/fisher_rao_filter.py` - Core anti-spam logic utilizing Jones invariants.
-   **Middleware:** `integrations/email/fisher_rao_middleware.py` - Pluggable component for SMTP servers (e.g., Postfix).