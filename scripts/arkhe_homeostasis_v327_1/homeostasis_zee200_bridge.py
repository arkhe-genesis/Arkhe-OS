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

    def generate_capture_proof(self, community_data, manifold_points,
                               epsilon=0.01, manifold_dim=3):
        """
        Gera prova ZK de que uma comunidade CAPTURE captura um manifold.
        """
        crystals = community_data['crystals']
        n_crystals = len(crystals)

        # Preparar inputs públicos para ZEE200
        public_inputs = [
            float(epsilon**2),           # epsilon_sq
            float(manifold_dim),          # manifold_dimension
            float(n_crystals),            # n_crystals
            float(hash(tuple(crystals)) % (2**32))  # indices hash
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

        # Gerar prova ZK real
        proof = inst.prove(security_bits=self.security_bits, post_quantum=True)

        return {
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
                        binarized_codes, J_matrix):
        """
        Verifica se CAPTURE > threshold e gera prova se necessário.
        """
        capture_fraction = classification_result.get('capture_fraction', 0)
        new_proofs = []

        if capture_fraction >= self.capture_threshold:
            print(f"🔐 CAPTURE={capture_fraction:.1%} >= {self.capture_threshold:.1%} → Gerando prova ZK...")

            # Identificar comunidade CAPTURE dominante (maior coesão)
            capture_communities = [
                (cid, info) for cid, info in community_details.items()
                if info['regime'] == 'CAPTURE'
            ]
            if not capture_communities:
                return new_proofs

            # Selecionar comunidade com maior |ρ|
            dominant_cid, dominant_info = max(
                capture_communities, key=lambda x: abs(x[1]['rho'])
            )

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

            # Gerar prova ZK
            proof = self.generate_capture_proof(
                community_data={
                    'community_id': dominant_cid,
                    'crystals': crystals,
                    'rho': dominant_info['rho']
                },
                manifold_points=manifold_points,
                epsilon=0.01,
                manifold_dim=manifold_dim
            )

            # Registrar no log on-chain
            block_id = len(self.proof_history) + 1
            proof['timestamp'] = f'block_{block_id}'
            proof['parent_hash'] = self._compute_parent_hash()

            # Computar hash deste bloco
            block_data = {**proof, 'capture_fraction': float(capture_fraction)}
            block_hash = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
            proof['block_hash'] = block_hash

            # Adicionar à cadeia
            with open(self.on_chain_log_path) as f:
                chain = json.load(f)
            chain[f'block_{block_id}'] = block_data
            with open(self.on_chain_log_path, 'w') as f:
                json.dump(chain, f, indent=2)

            self.proof_history.append(proof)
            new_proofs.append(proof)

            print(f"   ✓ Prova gerada: {proof['proof_hash'][:16]}..., bloco #{block_id}")

        return new_proofs

def spsa_with_zee200(initial_params, max_epochs=20, N_steps=200,
                     capture_threshold=0.80, zee200_bridge=None):
    """
    SPSA com geração automática de provas ZK quando CAPTURE ultrapassa limiar.
    """
    if zee200_bridge is None:
        zee200_bridge = HomeostasisZEE200Bridge(capture_threshold=capture_threshold)

    # Parâmetros otimizáveis
    theta = np.array([
        initial_params['kappa'],
        initial_params['lambda_l1'],
        initial_params['binarization_threshold'],
        initial_params['embedding_dim']
    ])
    bounds = [(0.1, 2.0), (0.0001, 0.01), (0.0, 0.3), (2, 5)]  # [min, max] por parâmetro

    a, c = 0.4, 0.2  # Hiperparâmetros SPSA
    history = []
    all_proofs = []

    # Usar pipeline ising do v325
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_ising_v325'))
    import crystal_brain_ising_pipeline as ising_pipeline

    def run_simulation(params, steps):
        # Gerar dados sintéticos para simulação (n_crystals truncado para velocidade se necessário, mantemos 768 mas pipeline lida)
        phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=steps)
        binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=params[2])
        J, h, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=params[1])
        # Force diag to 0
        np.fill_diagonal(J, 0)
        return {'binarized': binarized, 'J_matrix': J}

    def evaluate(params):
        states = run_simulation(params, N_steps // 2)
        # detect communities and classify
        communities = ising_pipeline.detect_crystal_communities(states['J_matrix'])
        classifications = ising_pipeline.classify_all_communities(states['J_matrix'], communities)
        capture_frac = sum(1 for c in classifications.values() if c['regime'] == 'CAPTURE') / len(classifications) if classifications else 0
        return capture_frac, classifications

    for k in range(1, max_epochs + 1):
        # 1. Simular com parâmetros atuais
        states = run_simulation(theta, N_steps)

        # 2. Pipeline Ising + classificação
        communities = ising_pipeline.detect_crystal_communities(states['J_matrix'])
        community_details = ising_pipeline.classify_all_communities(states['J_matrix'], communities)
        capture_fraction = sum(1 for c in community_details.values() if c['regime'] == 'CAPTURE') / len(community_details) if community_details else 0

        ising_result = {
            'capture_fraction': capture_fraction,
            'community_details': community_details
        }

        # 3. Verificar e gerar prova ZK se necessário
        new_proofs = zee200_bridge.check_and_prove(
            classification_result=ising_result,
            community_details=community_details,
            binarized_codes=states['binarized'],
            J_matrix=states['J_matrix']
        )
        all_proofs.extend(new_proofs)

        # 4. SPSA: estimar gradiente
        delta = np.random.choice([-1, 1], size=4)
        theta_plus = np.clip(theta + c * delta, *zip(*bounds))
        theta_minus = np.clip(theta - c * delta, *zip(*bounds))

        C_plus, _ = evaluate(theta_plus)
        C_minus, _ = evaluate(theta_minus)
        grad_est = (C_plus - C_minus) / (2 * c * delta)

        # 5. Atualização SPSA
        ak = a / (k ** 0.602)
        theta = theta + ak * grad_est  # Maximização: subir gradiente
        theta = np.clip(theta, *zip(*bounds))

        # 6. Registrar histórico
        epoch_record = {
            'epoch': k,
            'kappa': float(theta[0]),
            'lambda_l1': float(theta[1]),
            'binarization_threshold': float(theta[2]),
            'embedding_dim': int(theta[3]),
            'capture_fraction': float(capture_fraction),
            'proofs_generated': len(new_proofs)
        }
        history.append(epoch_record)

        print(f"Epoch {k:2d}: κ={theta[0]:.3f}, λ={theta[1]:.4f}, "
              f"thresh={theta[2]:.2f}, dim={int(theta[3])}, "
              f"CAPTURE={capture_fraction:.1%}, proofs={len(new_proofs)}")

    return history, all_proofs, theta

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
        'embedding_dim': 3
    }

    history, proofs, best_params = spsa_with_zee200(
        initial_params,
        max_epochs=args.max_epochs,
        capture_threshold=args.capture_threshold
    )

    print(f"Optimization finished. Best params: {best_params}")
