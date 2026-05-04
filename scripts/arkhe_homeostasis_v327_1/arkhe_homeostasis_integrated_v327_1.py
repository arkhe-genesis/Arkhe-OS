#!/usr/bin/env python3
"""
arkhe_homeostasis_integrated_v327_1.py

Integração de v327.1:
1. Homeostase (SPSA) + ZEE200 Bridge
2. Publicação contínua no dashboard
3. Steering de intenções verificável com ZEE200
4. Espaço de parâmetros expandido
"""

import numpy as np
import json
import os
import sys

# Garante acesso aos módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from homeostasis_zee200_bridge import HomeostasisZEE200Bridge
from living_interpretability_framework import LivingInterpretabilityPublisher
from verifiable_manifold_steering import VerifiableManifoldSteerer
from expanded_parameter_space import AdaptiveParameterOptimizer, multi_objective_score
from scripts.arkhe_homeostasis_v327_1.causal_efficacy_metrics import CausalEfficacyEvaluator

# Pipeline Ising
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arkhe_ising_v325'))
import crystal_brain_ising_pipeline as ising_pipeline

def homeostasis_with_expanded_steering(initial_params, param_ranges, intention_navigation_plan,
                              max_epochs=10, N_steps=200):
    """
    Combina otimização homeostática com espaço expandido e steering verificável de intenções.
    """
    # Inicializar componentes
    zee200_bridge = HomeostasisZEE200Bridge(capture_threshold=0.80)
    publisher = LivingInterpretabilityPublisher()

    # Otimizar parâmetros primeiro
    print("🧠 Fase 1: Otimização homeostática no espaço expandido...")

    def evaluate(params):
        # params: [kappa, lambda_l1, binarization_threshold, embedding_dim]
        phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=N_steps // 2)
        binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=params[2])
        J, h, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=params[1])
        np.fill_diagonal(J, 0)

        communities = ising_pipeline.detect_crystal_communities(J, search_enabled=True)
        classifications = ising_pipeline.classify_all_communities(J, communities)
        capture_frac = sum(1 for c in classifications.values() if c['regime'] == 'CAPTURE') / len(classifications) if classifications else 0

        result = {
            'capture_fraction': capture_frac,
            'community_details': classifications
        }

        # Check ZEE200 proof trigger
        zee200_bridge.check_and_prove(
            classification_result=result,
            community_details=classifications,
            binarized_codes=binarized,
            J_matrix=J
        )

        return multi_objective_score(result)

    optimizer = AdaptiveParameterOptimizer(
        param_ranges=param_ranges,
        initial_point=initial_params,
        grid_refinement_interval=2
    )

    opt_history, best_params, best_score = optimizer.optimize(evaluate, max_epochs=max_epochs)

    # Mapear os melhores parâmetros de volta para os nomes
    best_params_dict = {
        name: val for name, val in zip(optimizer.param_names, best_params)
    }

    # Phase 2: Navegação de intenções com parâmetros otimizados
    print("\n🧭 Fase 2: Steering verificável de intenções...")
    steering_results = []

    for i, (start_int, end_int) in enumerate(intention_navigation_plan):
        print(f"  Navegando intenção {i+1}/{len(intention_navigation_plan)}...")

        # Simular e encontrar manifold atual
        phases = ising_pipeline.generate_synthetic_crystal_data(n_timesteps=N_steps // 2)
        binarized = ising_pipeline.binarize_crystal_phases(phases, threshold=best_params_dict['binarization_threshold'])
        J, _, _ = ising_pipeline.fit_ising_crystal(binarized, gamma=best_params_dict['lambda_l1'])
        np.fill_diagonal(J, 0)

        communities = ising_pipeline.detect_crystal_communities(J, search_enabled=True)
        ising_result = ising_pipeline.classify_all_communities(J, communities)

        capture_communities = [
            (cid, info) for cid, info in ising_result.items()
            if info['regime'] == 'CAPTURE'
        ]

        if not capture_communities:
            print("   ⚠️  Nenhuma comunidade CAPTURE — pulando steering")
            continue

        # Selecionar comunidade dominante
        dominant_cid, dominant_info = max(capture_communities, key=lambda x: abs(x[1]['rho']))

        # Preparar dados do manifold
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

        # Executar steering com verificação
        steerer = VerifiableManifoldSteerer(manifold_data)

        # Projetar intenções completas (768) para subset de cristais da comunidade
        start_int_sub = np.array(start_int)[crystals]
        end_int_sub = np.array(end_int)[crystals]

        steering_result = steerer.steer_with_verification(
            start_int_sub, end_int_sub, n_steps=20, generate_proof=True
        )

        # Measure causal efficacy
        evaluator = CausalEfficacyEvaluator(baseline_window=20, coherence_metric='global_order_parameter')
        efficacy_metrics = evaluator.evaluate_steering_impact(
            pre_state=start_int_sub,
            post_state=steering_result['trajectory'][-1] if steering_result['trajectory'] else end_int_sub,
            steering_trajectory=steering_result['trajectory'] if steering_result['trajectory'] else [],
            target_intention=end_int_sub,
            non_target_communities=[] # Dummy for now
        )

        steering_results.append({
            'intention_pair_idx': i,
            'community_id': dominant_cid,
            'trajectory': steering_result,
            'causal_efficacy': efficacy_metrics.overall_efficacy,
            'proof_hash': steering_result['proof']['proof_hash'] if steering_result['proof'] else None
        })

        # Publicar evidência periódica
        if i % 2 == 0:
            evidence = publisher.generate_geometric_evidence(
                epoch_data={'epoch': max_epochs + i, **best_params_dict},
                ising_result={'capture_fraction': len(capture_communities) / len(ising_result), 'community_details': ising_result},
                optimization_history=opt_history,
                zee200_proofs=[steering_result['proof']] if steering_result['proof'] else None
            )
            publisher.publish_evidence(evidence)

    print("\n✅ Autonomia Geométrica Concluída. Evidências publicadas em publish/interpretability.")

if __name__ == '__main__':
    # Initial parameters
    initial_params = {
        'kappa': 0.75,
        'lambda_l1': 0.003,
        'binarization_threshold': 0.1,
        'embedding_dim': 3
    }

    param_ranges = {
        'kappa': (0.1, 2.0),
        'lambda_l1': (0.0001, 0.01),
        'binarization_threshold': (0.0, 0.3),
        'embedding_dim': (2, 5)
    }

    # Synthetic intention vectors (len 768 to match synthetic generated data default)
    n_crystals = 768
    intention_plan = [
        (np.random.randn(n_crystals).tolist(), np.random.randn(n_crystals).tolist()),
        (np.random.randn(n_crystals).tolist(), np.random.randn(n_crystals).tolist())
    ]

    # We run fewer epochs to keep testing time small. The optimization handles it nicely.
    homeostasis_with_expanded_steering(initial_params, param_ranges, intention_plan, max_epochs=2, N_steps=100)
