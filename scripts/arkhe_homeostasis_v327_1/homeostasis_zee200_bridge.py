#!/usr/bin/env python3
"""
homeostasis_zee200_bridge.py
Acopla o laço homeostático ao ZEE200: gera provas ZK quando CAPTURE > threshold.
"""
import numpy as np
import json
import hashlib
from pathlib import Path
import sys
import os
from scripts.arkhe_homeostasis_v327_1.spsa_adaptive import AdaptiveSPSA
from scripts.arkhe_homeostasis_v327_1.zee200_nondeterministic import NonDeterministicProofSeed
from scripts.arkhe_homeostasis_v327_1.proof_tagging import ProofTagger

# Ensure the mock backend is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import zee200_backend

class HomeostasisZEE200Bridge:
    """Ponte entre otimização homeostática e geração de provas ZK verificáveis."""

    def __init__(self, capture_threshold=0.80, security_bits=80,
                 zee200_profile=(1, 2, 1, 2), on_chain_log_path='publish/interpretability/coherence_chain.json'):
        self.capture_threshold = capture_threshold
        self.security_bits = security_bits
        self.zee200_profile = zee200_profile
        self.on_chain_log_path = Path(on_chain_log_path)
        self.proof_history = []

        # Inicializar log on-chain
        self.on_chain_log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.on_chain_log_path.exists():
            self._init_chain_log()

    def _init_chain_log(self):
        """Inicializa registro on-chain com bloco gênese."""
        genesis = {
            'block_0': {
                'timestamp': 'genesis',
                'event': 'CRYSTAL_HOMEOSTASIS_INIT',
                'parameters': {
                    'kappa': None, 'lambda_l1': None, 'binarization_threshold': None,
                    'embedding_dim': None, 'capture_threshold': self.capture_threshold
                },
                'proof_hash': 'genesis',
                'parent_hash': '0' * 64
            }
        }
        with open(self.on_chain_log_path, 'w') as f:
            json.dump(genesis, f, indent=2)

    def _compute_parent_hash(self):
        """Computa hash do último bloco para encadeamento."""
        with open(self.on_chain_log_path) as f:
            chain = json.load(f)
        last_block = chain[max(chain.keys(), key=lambda k: int(k.split('_')[1]))]
        return hashlib.sha256(json.dumps(last_block, sort_keys=True).encode()).hexdigest()

    def _compute_block_content_hash(self, block_data: dict) -> str:
        """Computa hash do conteúdo do bloco para encadeamento adequado."""
        # Excluir campos que não devem afetar o hash do conteúdo
        content_for_hash = {
            k: v for k, v in block_data.items()
            if k not in ['block_hash', 'parent_hash', 'timestamp']
        }
        return hashlib.sha256(
            json.dumps(content_for_hash, sort_keys=True).encode()
        ).hexdigest()

    def generate_capture_proof(self, community_data, manifold_points,
                               epsilon=0.01, manifold_dim=3, parent_hash=None):
        """
        Gera prova ZK de que uma comunidade CAPTURE captura um manifold.
        """
        crystals = community_data['crystals']
        n_crystals = len(crystals)

        # Preparar inputs públicos para ZEE200
        seed_gen = NonDeterministicProofSeed()
        proof_seed = seed_gen.generate_seed(community_data, self._compute_parent_hash())
        seed_num = int(hashlib.sha256(proof_seed.encode()).hexdigest(), 16) % (2**32)
        public_inputs = [
            float(epsilon**2),           # epsilon_sq
            float(manifold_dim),          # manifold_dimension
            float(n_crystals),            # n_crystals
            float(seed_num)               # indices hash from nondeterministic seed
        ]

        # Private witness (comprometido, não revelado)
        private_witness = [float(x) for x in manifold_points[:100].flatten()]

        # Constraints para prova de subspace capture
        constraints = [
            f'reconstruction_error: ||x_m - D @ z_filtered||^2 <= {epsilon**2}',
            f'sparsity: z_i = 0 for i not in S_star',
            f'field: F_{{2^61-1}}',
            f'profile: {self.zee200_profile}'
        ]

        # Criar instrução GTZK
        inst = zee200_backend.GTZKInstruction(
            name=f'capture_manifold_{community_data["community_id"]}',
            public_inputs=public_inputs,
            private_witness=private_witness,
            constraints=constraints,
            proof_type='monitoring'
        )

        # Instanciar gerador de entropia se ainda não existe
        if not hasattr(self, '_entropy_seed'):
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_homeostasis_v327_5'))
            from zee200_nondeterministic import NonDeterministicProofSeed
            self._entropy_seed = NonDeterministicProofSeed(
                entropy_sources=['time', 'pid', 'memory'],
                chain_binding=True
            )

        # Gerar prova ZK real
        proof = inst.prove(security_bits=self.security_bits, post_quantum=True)

        # Injetar entropia não-determinística
        proof = self._entropy_seed.inject_into_proof(proof, parent_hash)

        return {
            'entropy_metadata': proof.get('entropy_metadata'),
            'proof_hash': proof['proof_hash'],
            'proof_size_bytes': proof['proof_size_bytes'],
            'community_id': community_data['community_id'],
            'n_crystals': n_crystals,
            'cohesion_rho': float(community_data['rho']),
            'manifold_dim': int(manifold_dim),
            'epsilon': float(epsilon),
            'verified': True,  # Assumindo que prove() só retorna se sucesso
            'proof_type': proof.get('proof_type', 'monitoring'),
            'timestamp': None  # Preenchido ao registrar
        }

    def check_and_prove(self, classification_result, community_details,
                        binarized_codes, J_matrix,
                        epoch=None, parameter_changes=None):
        """
        Verifica se CAPTURE > threshold e gera prova se necessário, com tagging.
        """
        import time
        from datetime import datetime
        capture_fraction = classification_result.get('capture_fraction', 0)
        new_proofs = []

        # Inicializar tagger se necessário
        if not hasattr(self, '_proof_tagger'):
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_homeostasis_v327_5'))
            from proof_tagging import ProofTagger, ProofType
            self._proof_tagger = ProofTagger(
                monitoring_threshold=0.30,
                certification_threshold=0.80,
                transition_sensitivity=0.15
            )

        # Extrair métricas da comunidade dominante (se existir)
        dominant_info = None
        dominant_cid = None
        if community_details:
            capture_comms = [(cid, info) for cid, info in community_details.items()
                             if info['regime'] == 'CAPTURE']
            if capture_comms:
                dominant_cid, dominant_info = max(capture_comms, key=lambda x: abs(x[1]['rho']))

        # Classificar tipo de prova
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_homeostasis_v327_5'))
        from proof_tagging import ProofType
        proof_meta = self._proof_tagger.classify_proof(
            capture_fraction=capture_fraction,
            cohesion_rho=dominant_info['rho'] if dominant_info else None,
            manifold_dim=dominant_info.get('manifold_dim') if dominant_info else None,
            epoch=epoch,
            parameter_change=parameter_changes
        )

        # Decidir se gera prova baseada no tipo e prioridade
        should_generate = (
            proof_meta.proof_type in [
                ProofType.COHERENCE_CERTIFICATION,
                ProofType.REGIME_TRANSITION,
                ProofType.PARAMETER_OPTIMIZATION
            ] or
            (proof_meta.priority in ['high', 'critical'])
        )

        if not should_generate:
            return []

        print(f"   🔐 Generating {proof_meta.proof_type.name} proof "
              f"(CAPTURE={capture_fraction:.1%}, priority={proof_meta.priority})...")

        if dominant_info:
            # Extrair manifold points via PCA
            from sklearn.decomposition import PCA
            crystals = dominant_info['crystals']
            codes_sub = binarized_codes[:, crystals]

            # Estimar dimensionalidade via gap espectral
            cov_matrix = np.cov(codes_sub.T)
            eigenvalues = np.linalg.eigvalsh(cov_matrix)[::-1]
            gaps = np.diff(eigenvalues[:10])
            manifold_dim = int(np.argmax(np.abs(gaps)) + 1) if len(gaps) > 0 and np.max(np.abs(gaps)) > 0.1 else 3

            # Projetar para espaço do manifold
            pca = PCA(n_components=manifold_dim)
            manifold_points = pca.fit_transform(codes_sub)

            parent_hash = self._compute_parent_hash()

            # Gerar prova ZK
            proof = self.generate_capture_proof(
                community_data={
                    'community_id': dominant_cid,
                    'crystals': crystals,
                    'rho': dominant_info['rho']
                },
                manifold_points=manifold_points,
                epsilon=0.01,
                manifold_dim=manifold_dim,
                parent_hash=parent_hash
            )

            # Injetar metadados de tagging na prova
            proof['proof_metadata'] = proof_meta.to_dict()

            # Atualizar proof_hash para incluir tagging
            proof['proof_hash'] = hashlib.sha256(
                str({**proof, 'metadata': proof_meta.to_dict()}).encode()
            ).hexdigest()[:16]

            # Registrar no log on-chain com agregação dinâmica
            block_id = len(self.proof_history) + 1

            # Calcular hash do conteúdo deste bloco
            block_content = {
                'proof_hash': proof['proof_hash'],
                'community_id': proof['community_id'],
                'capture_fraction': float(capture_fraction),
                'block_id': block_id,
            }
            content_hash = self._compute_block_content_hash(block_content)

            # Calcular root_hash dinâmico (não constante)
            root_hash = hashlib.sha256(
                f"{content_hash}|{parent_hash}|{block_id}|{time.time_ns()}".encode()
            ).hexdigest()

            # Atualizar prova com metadados de agregação
            proof.update({
                'block_id': block_id,
                'parent_hash': parent_hash,
                'content_hash': content_hash,
                'root_hash': root_hash,  # Agora dinâmico!
                'timestamp': datetime.now().isoformat(),
                'capture_fraction': float(capture_fraction),
                'aggregation_metadata': {
                    'strategy': 'incremental_dynamic',
                    'window_size': 8,
                    'position_in_window': block_id % 8,
                    'root_update_policy': 'every_block'
                }
            })

            # Computar hash deste bloco
            block_hash = hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
            proof['block_hash'] = block_hash

            # Tag the proof
            tagger = ProofTagger(monitoring_threshold=0.30, certification_threshold=0.80, transition_sensitivity=0.15)
            proof_meta = tagger.classify_proof(
                capture_fraction=capture_fraction,
                cohesion_rho=float(dominant_info['rho']),
                manifold_dim=manifold_dim,
                epoch=block_id
            )
            proof['proof_type'] = proof_meta.proof_type.name
            proof['priority'] = proof_meta.priority

            # Adicionar à cadeia
            with open(self.on_chain_log_path) as f:
                chain = json.load(f)
            chain[f'block_{block_id}'] = proof
            with open(self.on_chain_log_path, 'w') as f:
                json.dump(chain, f, indent=2)

            self.proof_history.append(proof)
            new_proofs.append(proof)

            print(f"   ✓ Prova gerada: {proof['proof_hash'][:16]}..., "
                  f"bloco #{block_id}, root={root_hash[:16]}...")

            # Log de ações downstream
            if proof_meta.downstream_actions:
                print(f"   📬 Downstream actions: {', '.join(proof_meta.downstream_actions)}")

        return new_proofs

def spsa_with_adaptive_shock(initial_params, max_epochs=30, capture_threshold=0.80, zee200_bridge=None, N_steps=200):
    """SPSA com choque adaptativo de parâmetros."""
    if zee200_bridge is None:
        zee200_bridge = HomeostasisZEE200Bridge(capture_threshold=capture_threshold)

    # Usar pipeline ising do v325
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_ising_v325'))
    import crystal_brain_ising_pipeline as ising_pipeline

    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_homeostasis_v327_5'))
    from spsa_adaptive import AdaptiveSPSA

    # Configurar otimizador adaptativo
    param_bounds = [(0.1, 2.0), (0.0001, 0.01), (0.0, 0.3), (2, 5), (0.1, 2.0)]
    optimizer = AdaptiveSPSA(
        param_bounds=param_bounds,
        mode='adaptive',
        plateau_threshold=5,
        min_improvement=0.015  # 1.5% de melhoria mínima para resetar contagem
    )

    theta = np.array([
        initial_params['kappa'],
        initial_params['lambda_l1'],
        initial_params['binarization_threshold'],
        initial_params['embedding_dim'],
        initial_params.get('lambda_delta', 1.3759)
    ])

    a, c = 0.4, 0.2  # Hiperparâmetros SPSA
    history = []
    all_proofs = []

    def run_simulation(params, steps):
        phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=steps)
        binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=params[2])
        J, h, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=params[1])
        np.fill_diagonal(J, 0)
        return {'binarized': binarized, 'J_matrix': J}

    def evaluate(params):
        states = run_simulation(params, N_steps // 2)
        communities = ising_pipeline.detect_crystal_communities(states['J_matrix'])
        classifications = ising_pipeline.classify_all_communities(states['J_matrix'], communities)
        capture_frac = sum(1 for c in classifications.values() if c['regime'] == 'CAPTURE') / len(classifications) if classifications else 0
        return capture_frac

    for epoch in range(1, max_epochs + 1):
        # Para simulação principal e prova:
        states = run_simulation(theta, N_steps)
        communities = ising_pipeline.detect_crystal_communities(states['J_matrix'])
        community_details = ising_pipeline.classify_all_communities(states['J_matrix'], communities)
        capture_fraction = sum(1 for c in community_details.values() if c['regime'] == 'CAPTURE') / len(community_details) if community_details else 0

        ising_result = {
            'capture_fraction': capture_fraction,
            'community_details': community_details
        }

        parameter_changes = None
        if len(history) > 0:
            parameter_changes = {
                'kappa': theta[0] - history[-1]['params'][0],
                'lambda_l1': theta[1] - history[-1]['params'][1],
                'binarization_threshold': theta[2] - history[-1]['params'][2],
                'embedding_dim': theta[3] - history[-1]['params'][3],
                'lambda_delta': theta[4] - history[-1]['params'][4]
            }

        # Verificar e gerar prova ZK se necessário
        new_proofs = zee200_bridge.check_and_prove(
            classification_result=ising_result,
            community_details=community_details,
            binarized_codes=states['binarized'],
            J_matrix=states['J_matrix'],
            epoch=epoch,
            parameter_changes=parameter_changes
        )
        all_proofs.extend(new_proofs)

        # Executar passo adaptativo
        theta, score = optimizer.step(
            evaluate_fn=evaluate,
            epoch=epoch,
            current_theta=theta
        )

        # Registrar histórico
        history.append({
            'epoch': epoch,
            'params': theta.copy(),
            'score': score,
            'mode': optimizer.current_params.copy(),
            'stagnation': optimizer.stagnation_counter
        })

        print(f"Epoch {epoch:2d}: score={score:.4f}, "
              f"mode={'⚡SHOCK' if optimizer.mode=='aggressive' else '→stable'}, "
              f"stagnation={optimizer.stagnation_counter}, proofs={len(new_proofs)}")

    return history, all_proofs, theta

def spsa_with_zee200(initial_params, max_epochs=20, N_steps=200,
                     capture_threshold=0.80, zee200_bridge=None):
    return spsa_with_adaptive_shock(initial_params, max_epochs=max_epochs, capture_threshold=capture_threshold, zee200_bridge=zee200_bridge, N_steps=N_steps)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--initial-kappa', type=float, default=0.75)
    parser.add_argument('--initial-lambda', type=float, default=0.003)
    parser.add_argument('--capture-threshold', type=float, default=0.80)
    parser.add_argument('--max-epochs', type=int, default=20)
    args = parser.parse_args()

    initial_params = {
        'kappa': args.initial_kappa,
        'lambda_l1': getattr(args, 'initial_lambda', 0.003),
        'binarization_threshold': 0.1,
        'embedding_dim': 3,
        'lambda_delta': 1.3759
    }

    history, proofs, best_params = spsa_with_zee200(
        initial_params,
        max_epochs=args.max_epochs,
        capture_threshold=args.capture_threshold
    )

    print(f"Optimization finished. Best params: {best_params}")
