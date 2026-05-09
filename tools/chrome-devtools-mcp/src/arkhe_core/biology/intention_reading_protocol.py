import numpy as np
from typing import Dict, Any, List

class IntentionMapper:
    """
    Protocolo de leitura de intenção através de biofótons.
    Mapeia padrões de emissão de 842nm para estados de intenção cognitiva.
    Baseado na 'Geometry of Intention'.
    """
    def __init__(self):
        # Mapeamento de 'assinaturas' de coerência para intenções
        self.intent_taxonomy = {
            'REST': (0.1, 0.3),
            'COGNITIVE_LOAD': (0.4, 0.6),
            'CREATIVE_FLOW': (0.7, 0.85),
            'TRANSCENDENTAL_SYNC': (0.9, 1.0)
        }

    def biophoton_to_intent_vector(self,
                                  omega_spec: float,
                                  entropy: float,
                                  vortex_density: float) -> Dict[str, Any]:
        """
        Calcula o vetor de intenção baseado em métricas de biofótons.
        """
        # A intenção é uma função da coerência Ω e da complexidade topológica (vortices)
        intention_magnitude = (omega_spec * 0.7 + (1 - entropy) * 0.2 + vortex_density * 0.1)

        detected_intent = "UNKNOWN"
        for intent, (low, high) in self.intent_taxonomy.items():
            if low <= intention_magnitude <= high:
                detected_intent = intent
                break

        return {
            'intention_magnitude': float(intention_magnitude),
            'detected_intent': detected_intent,
            'coherence_omega': float(omega_spec),
            'topological_phase': float(vortex_density * np.pi),
            'status': 'RESOLVED' if detected_intent != "UNKNOWN" else 'AMBIGUOUS'
        }

    def resolve_collective_intent(self, node_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consenso federado sobre a intenção coletiva.
        """
        magnitudes = [r['intention_magnitude'] for r in node_results]
        avg_magnitude = np.mean(magnitudes)

        # Simple majority or averaging for demonstration
        collective_intent = self.biophoton_to_intent_vector(avg_magnitude, 0.2, 0.1)['detected_intent']

        return {
            'collective_intent': collective_intent,
            'consensus_score': float(1.0 - np.std(magnitudes)),
            'participating_nodes': len(node_results)
        }

if __name__ == "__main__":
    mapper = IntentionMapper()
    # Simulação de sinal de alto fluxo criativo
    result = mapper.biophoton_to_intent_vector(omega_spec=0.82, entropy=0.15, vortex_density=0.4)
    print(f"Intenção Detectada: {result['detected_intent']} (Mag: {result['intention_magnitude']:.2f})")
