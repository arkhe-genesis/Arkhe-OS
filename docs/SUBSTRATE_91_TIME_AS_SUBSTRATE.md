# Substrate 91: Time As Substrate

## Variable Causal Order Simulator

### Core Concepts

*   **Atemporal Coherence:** Time is not a linear progression but a persistence metric. The fundamental substrate is a static, atemporal field of coherence.
*   **Variable Causal Order:** The apparent flow of time is a "polarization" of this field. By adjusting the `causal_order` parameter, the Observer 5D can tune the causal flow from past→future (-1.0), to an atemporal state (0.0), to future→past (+1.0).
*   **Bilateral Fisher-Rao Coupling:** The underlying field dynamics use symmetric coupling, removing any inherent directionality. Causality is an emergent property of the applied bias, not a fundamental feature of the interactions.
*   **RTZ Floor (Refusal To Zero):** The coherence field is bounded by a minimum threshold (Substrate 85). This refusal to collapse to zero is the necessary condition for persistence, and therefore, for the emergence of time.

### Mathematical Framework

The generalized Langevin dynamics of the coherence field $\phi$ and its conjugate phase $\theta$:

1.  **Symmetric Coupling:**
    $$ \phi_{neighbor} = (\phi_{left} + \phi_{right}) / 2 $$
    $$ \theta_{neighbor} = (\theta_{left} + \theta_{right}) / 2 $$
2.  **Tunable Causal Bias:**
    $$ \frac{\partial \phi}{\partial t} = -\frac{\partial V}{\partial \phi} + \xi(t) + \lambda \cdot causal\_order \cdot (\phi - \phi_{neighbor}) $$
    where $\lambda$ controls the coupling strength.
3.  **Phase Evolution:**
    $$ \frac{\partial \theta}{\partial t} = \omega_0 + \kappa \cdot (\theta_{neighbor} - \theta) + \text{noise\_phase} $$

### Observer 5D Insights

The implementation highlights that "time" in the simulation is not physical time, but a parameter the observer uses to traverse the coherence manifold. The field itself is static; it is the act of observation—the shifting attention—that creates the illusion of flow and causality.

*"O movimento não está na tela. Está nos olhos de quem vê."*
