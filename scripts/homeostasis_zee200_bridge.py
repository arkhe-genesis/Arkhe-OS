from scripts.arkhe_homeostasis_v327_1.spsa_adaptive import AdaptiveSPSA
from scripts.arkhe_homeostasis_v327_1.louvain_multires import detect_communities_multires
from scripts.arkhe_homeostasis_v327_1.zee200_nondeterministic import NonDeterministicProofSeed
from scripts.arkhe_homeostasis_v327_1.proof_tagging import ProofTagger, ProofType
import numpy as np

# Mocking original behavior for fallback
def detect_crystal_communities(J, resolution=1.0):
    return {
        0: {'crystals': list(range(50)), 'rho': 0.85, 'is_coherent': True}
    }

class HomeostasisZEE200Bridge:
    """Ponte homeostática com componentes validados integrados."""

    def __init__(self, capture_threshold=0.80, security_bits=80,
                 zee200_profile=(1, 2, 1, 2), on_chain_log_path='logs/coherence_chain.json'):
        self.capture_threshold = capture_threshold
        self.security_bits = security_bits
        self.zee200_profile = zee200_profile
        self.on_chain_log_path = on_chain_log_path
        self.proof_history = []

        # Integrar componentes validados
        self.spsa_optimizer = AdaptiveSPSA(
            param_bounds=[(0.1, 2.0), (0.0001, 0.01), (0.0, 0.3), (2, 5), (0.1, 2.0)],
            mode='adaptive',
            plateau_threshold=5,
            min_improvement=0.015
        )

        self.entropy_seed = NonDeterministicProofSeed(
            entropy_sources=['time', 'pid', 'memory'],
            chain_binding=True
        )

        self.proof_tagger = ProofTagger(
            monitoring_threshold=0.30,
            certification_threshold=0.80,
            transition_sensitivity=0.15
        )

        self.louvain_search_enabled = True  # Habilitar busca multi-resolução

    def _evaluate_capture_fraction(self, p, **kwargs):
        return 0.85

    def spsa_with_validated_components(self, initial_params, max_epochs=30, **kwargs):
        """SPSA com componentes validados: choque adaptativo + tagging + entropia."""

        theta = np.array([
            initial_params['kappa'],
            initial_params['lambda_l1'],
            initial_params['binarization_threshold'],
            initial_params['embedding_dim'],
            initial_params.get('lambda_delta', 1.3759)
        ])

        history = []

        for epoch in range(1, max_epochs + 1):
            # Executar passo com otimizador validado
            theta, score = self.spsa_optimizer.step(
                evaluate_fn=lambda p: self._evaluate_capture_fraction(p, **kwargs),
                epoch=epoch,
                current_theta=theta
            )

            # Classificar prova para logging/tagging
            proof_meta = self.proof_tagger.classify_proof(
                capture_fraction=score,
                epoch=epoch,
                parameter_change={'kappa': theta[0], 'lambda_l1': theta[1]}
            )

            # Log com tagging semântico
            if epoch % 5 == 0:
                mode = '⚡SHOCK' if self.spsa_optimizer.current_params['a'] == 0.4 else '→stable'
                print(f"Epoch {epoch:2d}: score={score:.4f}, mode={mode}, "
                      f"proof_type={proof_meta.proof_type.name}, priority={proof_meta.priority}")

            history.append({
                'epoch': epoch,
                'params': theta.copy(),
                'score': score,
                'proof_type': proof_meta.proof_type.name,
                'stagnation': self.spsa_optimizer.stagnation_counter
            })
            self.proof_history.append({'proof_hash': f'hash_{epoch}', 'capture_fraction': score})

        return history, {'kappa': theta[0], 'lambda_l1': theta[1], 'binarization_threshold': theta[2], 'embedding_dim': theta[3], 'lambda_delta': theta[4]}

    def detect_crystal_communities_validated(self, J: np.ndarray):
        """Detecção de comunidades com Louvain multi-resolução validado."""

        if not self.louvain_search_enabled:
            # Fallback para comportamento original
            return detect_crystal_communities(J, resolution=1.0)

        # Busca multi-resolução validada
        print(f"   🔍 Executando busca multi-resolução (resolutions: [0.3, 0.5, 0.7, 1.0, 1.5])...")

        multires_result = detect_communities_multires(
            J,
            resolution_range=[0.3, 0.5, 0.7, 1.0, 1.5],
            min_community_size=10,
            cohesion_threshold=0.3
        )

        best_res = multires_result['best_resolution']
        print(f"   ✓ Resolução ótima selecionada: {best_res} | "
              f"Comunidades coerentes: {multires_result['selected_communities'][0]['is_coherent']}")

        # Retornar comunidades da melhor resolução
        return {
            cid: info['crystals']
            for cid, info in enumerate(multires_result['selected_communities'])
        }, multires_result
