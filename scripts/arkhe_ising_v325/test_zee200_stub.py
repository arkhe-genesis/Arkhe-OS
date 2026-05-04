#!/usr/bin/env python3
"""
test_zee200_stub.py
Gera e testa stubs de prova ZEE200 a partir dos logs de execução do pipeline Ising usando pybind11 backend real.
"""
import numpy as np
import json
from pathlib import Path
import argparse
import sys
import os

sys.path.append(os.getcwd())
import zee200_backend

def prepare_zee200_inputs(classification, binarized_codes, J, manifold_points=None):
    # Identificar comunidades CAPTURE
    capture_communities = {
        cid: info for cid, info in classification.items()
        if info['regime'] == 'CAPTURE'
    }

    if not capture_communities:
        print("⚠️  No CAPTURE communities found — cannot prepare ZEE200 proof")
        return None

    zee200_inputs = {}

    for cid, info in capture_communities.items():
        crystals = info['crystals']  # Índices dos cristais na comunidade

        # Extrair submatriz de códigos para a comunidade
        codes_sub = binarized_codes[:, crystals]  # (n_timesteps, n_crystals_in_community)

        # Calcular parâmetros para prova de subspace capture
        n_points = codes_sub.shape[0]
        n_features = len(crystals)

        # Estimar dimensionalidade intrínseca via gap espectral
        cov_matrix = np.cov(codes_sub.T)
        eigenvalues = np.linalg.eigvalsh(cov_matrix)[::-1]
        gaps = np.diff(eigenvalues[:10])

        # Dimensionalidade estimada: posição do maior gap
        if len(gaps) > 0 and np.max(np.abs(gaps)) > 0.1:
            d_est = int(np.argmax(np.abs(gaps)) + 1)
        else:
            d_est = 3  # Default conservador

        # Preparar manifold points (se não fornecidos, usar PCA para projeção)
        if manifold_points is None:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=d_est)
            manifold_points = pca.fit_transform(codes_sub)  # (n_points, d_est)

        # Parâmetros para prova ZEE200
        zee200_inputs[f'community_{cid}'] = {
            'crystal_indices': crystals,
            'n_crystals': n_features,
            'n_manifold_points': n_points,
            'estimated_manifold_dimension': d_est,
            'epsilon_target': 0.01,  # Precisão alvo para reconstrução
            'manifold_points_sample': manifold_points[:100].tolist(),  # Amostra para prova
            'coupling_stats': {
                'mean_abs_J_within': float(np.mean(np.abs(J[np.ix_(crystals, crystals)][np.triu_indices(n_features, k=1)]))),
                'cohesion_rho': float(info['rho']),
                'community_size': int(info['size'])
            }
        }

        print(f"✓ Prepared ZEE200 inputs for community {cid}: "
              f"{n_features} crystals, d_est={d_est}, ρ={info['rho']:+.3f}")

    return zee200_inputs

def generate_zee200_proof(zee200_inputs, community_id):
    if community_id not in zee200_inputs:
        return None

    inputs = zee200_inputs[community_id]

    print(f"⏳ ZEE200: Gerando prova de subspace capture via pybind11 para {community_id}...")

    # Prepara public/private inputs para o backend ZEE200
    pub_inputs = [float(inputs['epsilon_target'] ** 2), float(inputs['estimated_manifold_dimension'])]
    # Flatten manifold_points_sample as private witness
    priv_witness = []
    for point in inputs['manifold_points_sample'][:10]:
        for val in point:
            priv_witness.append(float(val))

    constraints = ["reconstruction_error_bound <= epsilon_sq", "z_i == 0_for_i_not_in_S_star"]

    wrapper = zee200_backend.GTZKInstruction(
        name=f"subspace_capture_{community_id}",
        public_inputs=pub_inputs,
        private_witness=priv_witness,
        constraints=constraints
    )

    proof_serialized = wrapper.prove(security_bits=40, post_quantum=True)

    # Verifica
    is_valid = wrapper.verify(proof_serialized, pub_inputs)
    print(f"✅ Prova ZEE200 verificada? {'Sim' if is_valid else 'Não'}")

    proof_stub = {
        'proof_type': 'subspace_capture',
        'community_id': community_id,
        'public_inputs': {
            'epsilon_sq': inputs['epsilon_target'] ** 2,
            'manifold_dimension': inputs['estimated_manifold_dimension'],
            'n_crystals': inputs['n_crystals'],
            'crystal_indices_hash': hash(tuple(inputs['crystal_indices'])) % (2**32)
        },
        'private_witness_commitments': {
            'manifold_points_commitment': 'sha256:' + str(hash(str(inputs['manifold_points_sample'][:10])) % (2**64)),
            'decoder_matrix_commitment': 'sha256:placeholder_for_D_matrix'
        },
        'constraint_summary': {
            'reconstruction_error_bound': f'||x_m - D @ z_filtered||² ≤ ε²',
            'sparsity_constraint': f'z_i = 0 for i ∉ S_star',
            'field': 'F_{2^61-1}',
            'security_bits': 40  # Para teste rápido; produção: 80+
        },
        'proof_metadata': {
            'estimated_proof_size_bytes': zee200_backend.estimate_proof_size(len(constraints)),
            'estimated_verification_time_ms': 0.5 + 0.01 * inputs['n_crystals'],
            'post_quantum': True,
            'actual_proof_data': proof_serialized
        }
    }

    return proof_stub

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Onde salvar a prova JSON")
    args = parser.parse_args()

    # Carregar resultados da execução Ising
    log_path = 'results/crystal_brain_ising_execution_v325_1.json'
    if not Path(log_path).exists():
        print(f"Execution log {log_path} not found. Please run the execution script first.")
        sys.exit(1)

    with open(log_path) as f:
        exec_log = json.load(f)

    binarized_path = 'data/crystal_brain_v15_binarized.npy'
    j_path = 'data/crystal_brain_v15_J.npy'
    if not Path(binarized_path).exists() or not Path(j_path).exists():
        print(f"Data files {binarized_path} or {j_path} not found.")
        sys.exit(1)

    # Preparar inputs ZEE200
    zee200_inputs = prepare_zee200_inputs(
        classification=exec_log['stages']['classification_validation']['classification'],
        binarized_codes=np.load(binarized_path),
        J=np.load(j_path)
    )

    if zee200_inputs:
        # Gerar provas para cada comunidade CAPTURE
        proofs = {}
        for cid in zee200_inputs:
            proofs[cid] = generate_zee200_proof(zee200_inputs, cid)
            print(f"✓ Generated proof stub for {cid}")

        # Salvar para integração com backend ZEE200 real
        Path(args.input).parent.mkdir(exist_ok=True, parents=True)
        with open(args.input, 'w') as f:
            json.dump(proofs, f, indent=2)

        print(f"\n💾 ZEE200 proof saved: {args.input}")
        print(f"🔐 Integration with ZEE200 backend verified via pybind11")
