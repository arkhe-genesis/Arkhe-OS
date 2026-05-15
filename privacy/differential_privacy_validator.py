import hashlib
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class DPReport:
    epsilon: float
    delta: float
    privacy_violation: bool
    proof_hash: Optional[str] = None

class DifferentialPrivacyEngine:
    """
    Substrato 180‑D: Mecanismo de privacidade diferencial e verificação.
    """
    def __init__(self, default_epsilon=1.0, default_delta=1e-5):
        self.epsilon = default_epsilon
        self.delta = default_delta

    def apply_dp(self, model_update: Dict, epsilon: float, delta: float) -> Dict:
        """
        Adiciona ruído Gaussiano calibrado para garantir (ε, δ)-DP.
        """
        # Extrai gradientes
        gradients = np.array(model_update['gradients'])
        # Calcula norma L2 dos gradientes para sensibilidade
        sensitivity = np.linalg.norm(gradients)
        if sensitivity == 0:
             sigma = 0
        else:
             sigma = (sensitivity * np.sqrt(2 * np.log(1.25 / delta))) / epsilon
        noise = np.random.normal(0, sigma, size=gradients.shape)
        noisy_gradients = gradients + noise
        safe_update = model_update.copy()
        safe_update['gradients'] = noisy_gradients.tolist()
        safe_update['privacy_params'] = {'epsilon': epsilon, 'delta': delta}
        return safe_update

    def validate_privacy(self, original_data_sample: list, released_model: Dict) -> DPReport:
        """
        Simula validação pós-hoc: verifica se o modelo liberado satisfaz
        os limites de privacidade declarados. Em produção, isso seria
        feito via ZK-proof de que o treinamento seguiu o protocolo DP.
        """
        # Placeholder para verificação real com ZK
        # Aqui, assumimos que o modelo veio com parâmetros e checamos consistência
        declared_eps = released_model.get('privacy_params', {}).get('epsilon')
        declared_delta = released_model.get('privacy_params', {}).get('delta')

        if declared_eps is None or declared_eps > self.epsilon:
            return DPReport(epsilon=declared_eps or 0, delta=declared_delta or 0,
                            privacy_violation=True, proof_hash=None)

        # Gera um hash de compromisso (simulando proof)
        proof_data = f"{original_data_sample}{released_model['gradients']}{declared_eps}{declared_delta}".encode()
        proof_hash = hashlib.sha3_256(proof_data).hexdigest()

        return DPReport(epsilon=declared_eps, delta=declared_delta,
                        privacy_violation=False, proof_hash=proof_hash)
