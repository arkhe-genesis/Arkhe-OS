#!/usr/bin/env python3
"""
run_integrated_homeostasis_real.py

Integração de v327.3:
1. Homeostase (SPSA) + ZEE200 Bridge (REAL)
2. Publicação contínua no dashboard
3. Steering de intenções verificável com ZEE200 (REAL)
4. Espaço de parâmetros expandido
"""

import numpy as np
import json
import os
import sys
import time

# Garante acesso aos módulos locais
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'arkhe_homeostasis_v327_1'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zee200_integration'))

from homeostasis_zee200_bridge import HomeostasisZEE200Bridge
from living_interpretability_framework import LivingInterpretabilityPublisher
from verifiable_manifold_steering import VerifiableManifoldSteerer
from expanded_parameter_space import AdaptiveParameterOptimizer, multi_objective_score

# Pipeline Ising
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'arkhe_ising_v325'))
import crystal_brain_ising_pipeline as ising_pipeline

def run_integrated_homeostasis_real(
    initial_params=None,
    max_epochs=20,
    N_steps=2000,
    capture_threshold=0.80,
    publish_dir='publish/interpretability',
    test_steering=True,
    use_real_zee200=True,  # NOVO: flag para backend real
    security_bits=80        # NOVO: bits de segurança para produção
):
    """
    Executa pipeline integrado COM backend ZEE200 real.
    """
    if initial_params is None:
        initial_params = {
            'kappa': 0.75,
            'lambda_l1': 0.003,
            'binarization_threshold': 0.15,
            'embedding_dim': 3
        }

    param_ranges = {
        'kappa': (0.1, 2.0),
        'lambda_l1': (0.0001, 0.01),
        'binarization_threshold': (0.0, 0.3),
        'embedding_dim': (2, 5)
    }

    # Inicializar bridge REAL se solicitado
    if use_real_zee200:
        from zee200_backend_real import RealZEE200Bridge
        zee200_bridge = RealZEE200Bridge(
            security_bits=security_bits,
            profile=(1, 2, 1, 2),
            post_quantum=True
        )
        print(f"   ✓ Real ZEE200 bridge initialized (security={security_bits}-bit, PQ={True})")
    else:
        # Fallback para mock (desenvolvimento)
        zee200_bridge = HomeostasisZEE200Bridge(
            capture_threshold=capture_threshold,
            security_bits=40
        )
        print(f"   ✓ Mock ZEE200 bridge initialized (security=40-bit)")

    publisher = LivingInterpretabilityPublisher(output_dir=publish_dir)

    print("🧠 Fase 1: Otimização homeostática no espaço expandido...")

    total_proofs_generated = 0
    proofs_list = []

    def evaluate(params):
        nonlocal total_proofs_generated
        # params: [kappa, lambda_l1, binarization_threshold, embedding_dim]
        phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=N_steps // 2)
        binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=params[2])
        J, h, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=params[1])
        np.fill_diagonal(J, 0)

        communities = ising_pipeline.detect_crystal_communities(J)
        classifications = ising_pipeline.classify_all_communities(J, communities)
        capture_frac = sum(1 for c in classifications.values() if c['regime'] == 'CAPTURE') / len(classifications) if classifications else 0

        result = {
            'capture_fraction': capture_frac,
            'community_details': classifications
        }

        if capture_frac >= capture_threshold and use_real_zee200:
            capture_communities = [
                (cid, info) for cid, info in classifications.items()
                if info['regime'] == 'CAPTURE'
            ]
            if capture_communities:
                dominant_cid, dominant_info = max(capture_communities, key=lambda x: abs(x[1]['rho']))

                from sklearn.decomposition import PCA
                crystals = dominant_info['crystals']
                codes_sub = binarized[:, crystals]

                manifold_dim = dominant_info.get('manifold_dim', int(params[3]))
                if type(manifold_dim) is not int or manifold_dim > min(codes_sub.shape):
                    manifold_dim = min(codes_sub.shape)

                pca = PCA(n_components=manifold_dim)
                manifold_points = pca.fit_transform(codes_sub)

                decoder_matrix = np.random.randn(768, manifold_dim) # mock decoder for the real wrapper API

                community_data = {
                    'community_id': dominant_cid,
                    'crystals': crystals,
                    'rho': dominant_info['rho']
                }

                proof = zee200_bridge.generate_capture_proof_real(
                    community_data=community_data,
                    manifold_points=manifold_points,
                    decoder_matrix=decoder_matrix,
                    epsilon=0.01
                )

                total_proofs_generated += 1
                proofs_list.append(proof)

                print(f"   ✓ Real proof: {proof['proof_time_ms']:.1f}ms, "
                      f"{proof['proof_size_bytes']/1024:.1f}KB, "
                      f"verify={proof['verify_time_ms']:.2f}ms")

        elif not use_real_zee200:
            # mock bridge behavior
             new_proofs = zee200_bridge.check_and_prove(
                classification_result=result,
                community_details=classifications,
                binarized_codes=binarized,
                J_matrix=J
            )
             total_proofs_generated += len(new_proofs)
             proofs_list.extend(new_proofs)


        return multi_objective_score(result)

    optimizer = AdaptiveParameterOptimizer(
        param_ranges=param_ranges,
        initial_point=initial_params,
        grid_refinement_interval=5
    )

    start_opt_time = time.time()
    opt_history, best_params, best_score = optimizer.optimize(evaluate, max_epochs=max_epochs)
    opt_time = time.time() - start_opt_time

    best_params_dict = {
        name: val for name, val in zip(optimizer.param_names, best_params)
    }

    steering_results = []
    if test_steering:
        print("\n🧭 Fase 2: Steering verificável de intenções...")
        n_crystals = 768
        intention_navigation_plan = [
            (np.random.randn(n_crystals).tolist(), np.random.randn(n_crystals).tolist())
            for _ in range(2)
        ]

        for i, (start_int, end_int) in enumerate(intention_navigation_plan):
            print(f"  Navegando intenção {i+1}/{len(intention_navigation_plan)}...")

            phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=N_steps // 2)
            binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=best_params_dict['binarization_threshold'])
            J, _, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=best_params_dict['lambda_l1'])
            np.fill_diagonal(J, 0)

            communities = ising_pipeline.detect_crystal_communities(J)
            ising_result = ising_pipeline.classify_all_communities(J, communities)

            capture_communities = [
                (cid, info) for cid, info in ising_result.items()
                if info['regime'] == 'CAPTURE'
            ]

            if not capture_communities:
                print("   ⚠️  Nenhuma comunidade CAPTURE — pulando steering")
                continue

            dominant_cid, dominant_info = max(capture_communities, key=lambda x: abs(x[1]['rho']))

            from sklearn.decomposition import PCA
            crystals = dominant_info['crystals']
            codes_sub = binarized[:, crystals]

            manifold_dim = dominant_info.get('manifold_dim', int(best_params_dict['embedding_dim']))
            if type(manifold_dim) is not int or manifold_dim > min(codes_sub.shape):
                manifold_dim = min(codes_sub.shape)

            pca = PCA(n_components=manifold_dim)
            manifold_points = pca.fit_transform(codes_sub)

            manifold_data = {
                'points': manifold_points,
                'crystals': crystals,
                'embedding': pca
            }

            steerer = VerifiableManifoldSteerer(manifold_data)

            start_int_sub = np.array(start_int)[crystals]
            end_int_sub = np.array(end_int)[crystals]

            steering_result = steerer.steer_with_verification(
                start_int_sub, end_int_sub, n_steps=20, generate_proof=True
            )

            steering_results.append({
                'intention_pair_idx': i,
                'community_id': dominant_cid,
                'trajectory': steering_result,
                'proof_hash': steering_result['proof']['proof_hash'] if steering_result['proof'] else None
            })

            if i % 2 == 0:
                evidence = publisher.generate_geometric_evidence(
                    epoch_data={'epoch': max_epochs + i, **best_params_dict},
                    ising_result={'capture_fraction': len(capture_communities) / len(ising_result), 'community_details': ising_result},
                    optimization_history=opt_history,
                    zee200_proofs=[steering_result['proof']] if steering_result['proof'] else None
                )
                publisher.publish_evidence(evidence)

    print("\n✅ Autonomia Geométrica Concluída. Evidências publicadas em publish/interpretability.")

    return {
        'optimization': {
            'total_proofs_generated': total_proofs_generated,
            'final_capture_fraction': best_score,
            'best_params': best_params_dict,
            'history': opt_history,
            'time': opt_time
        },
        'steering': {
            'n_pairs_tested': len(steering_results)
        },
        'proofs': proofs_list,
        'timestamp': time.time()
    }

if __name__ == '__main__':
    run_integrated_homeostasis_real(max_epochs=2, N_steps=100)
