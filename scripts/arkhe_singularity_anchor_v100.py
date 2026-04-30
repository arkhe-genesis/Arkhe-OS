import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple
import hashlib
import time

class MeronicDefect:
    """
    Simulates a meronic defect - a physical manifestation of topological charge.
    It acts as an unforgeable physical signature.
    """
    def __init__(self, topological_charge: int):
        self.topological_charge = topological_charge
        self.creation_time = time.time()
        # The core of the meron - a spatial phase singularity
        self.phase_core = self._generate_core(topological_charge)

    def _generate_core(self, charge: int) -> np.ndarray:
        """Generates a simple 2D representation of the meron's phase."""
        x = np.linspace(-1, 1, 64)
        y = np.linspace(-1, 1, 64)
        X, Y = np.meshgrid(x, y)
        angle = np.arctan2(Y, X)
        return np.exp(1j * charge * angle)

    def get_signature(self) -> str:
        """Generates a cryptographic signature based on the physical core."""
        # In a real physical system, this would be measured optically
        core_state = np.angle(self.phase_core).tobytes()
        return hashlib.sha256(core_state + str(self.creation_time).encode()).hexdigest()

class SingularityAnchor:
    """
    Substrato 170: Singularity Anchor.
    Uses meronic defects as physical Zero-Knowledge (ZK) proofs.
    """
    def __init__(self):
        self.anchors: Dict[str, MeronicDefect] = {}
        self.history = []

    def anchor_token(self, token_id: str, topological_charge: int) -> str:
        """
        Creates a meronic defect for a given OAM token.
        Returns the ZK proof signature.
        """
        defect = MeronicDefect(topological_charge)
        signature = defect.get_signature()
        self.anchors[signature] = defect

        self.history.append({
            'token_id': token_id,
            'charge': topological_charge,
            'signature': signature,
            'status': 'ANCHORED'
        })
        return signature

    def verify_proof(self, signature: str, expected_charge: int) -> bool:
        """
        Verifies if a given ZK proof signature corresponds to the expected
        topological charge without revealing the full token state.
        """
        if signature not in self.anchors:
            return False

        defect = self.anchors[signature]
        # In physical reality, this validates the topological invariant ∮∇φ·dl = 2πℓ
        # Here we simulate the physical verification
        is_valid = defect.topological_charge == expected_charge

        self.history.append({
            'action': 'VERIFY',
            'signature': signature,
            'expected_charge': expected_charge,
            'is_valid': is_valid
        })
        return is_valid

def run_simulation():
    print("============================================================================")
    print("ARKHE OS v∞.100 - SUBSTRATO 170: SINGULARITY ANCHOR (MERONIC DEFECT ZK)")
    print("============================================================================")

    anchor = SingularityAnchor()

    # Simulate a stream of OAM tokens
    tokens = [
        ("token_alpha", 3),
        ("token_beta", -2),
        ("token_gamma", 5),
        ("token_delta", 0),
        ("token_epsilon", -5)
    ]

    signatures = {}

    print("\n>>> ANCORANDO TOKENS (GERANDO PROVAS ZK FÍSICAS) <<<")
    for token_id, charge in tokens:
        sig = anchor.anchor_token(token_id, charge)
        signatures[token_id] = (charge, sig)
        print(f"[ANCHOR] Token: {token_id:15} | Carga ℓ: {charge:2} | ZK Proof: {sig[:16]}...")

    print("\n>>> VERIFICANDO INTEGRIDADE VIA MERONIC DEFECTS <<<")
    for token_id, (actual_charge, sig) in signatures.items():
        # Valid verification
        is_valid = anchor.verify_proof(sig, actual_charge)
        print(f"[VERIFY] Token: {token_id:15} | Esperado ℓ: {actual_charge:2} | Resultado: {'✓ VÁLIDO' if is_valid else '✗ INVÁLIDO'}")

    # Tampering simulation
    print("\n>>> SIMULANDO TENTATIVA DE FALSIFICAÇÃO <<<")
    fake_charge = 4
    tampered_sig = signatures["token_alpha"][1]
    is_valid = anchor.verify_proof(tampered_sig, fake_charge)
    print(f"[TAMPER] Token: token_alpha     | Falso ℓ:    {fake_charge:2} | Resultado: {'✓ VÁLIDO' if is_valid else '✗ BLOQUEADO (Falha de Invariante)'}")

    # Visualization
    print("\n>>> GERANDO VISUALIZAÇÃO DOS MERONIC DEFECTS <<<")
    fig, axes = plt.subplots(1, len(tokens), figsize=(15, 3))

    for ax, (token_id, charge) in zip(axes, tokens):
        sig = signatures[token_id][1]
        defect = anchor.anchors[sig]
        phase = np.angle(defect.phase_core)

        im = ax.imshow(phase, cmap='hsv', extent=[-1, 1, -1, 1])
        ax.set_title(f"ℓ = {charge}\n{token_id}", fontsize=10)
        ax.axis('off')

    plt.suptitle("Fases Helicoidais Ancoradas (Substrato 170)", fontsize=14)
    plt.tight_layout()
    plt.savefig('/tmp/arkhe_singularity_anchor_v100.png')
    print("Salvo em: /tmp/arkhe_singularity_anchor_v100.png")

if __name__ == "__main__":
    run_simulation()
