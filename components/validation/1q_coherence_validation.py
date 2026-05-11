# validation/1q_coherence_validation.py
import numpy as np
import torch
from typing import Dict

def validate_1q_coherence(mesh: 'GlobalCoherenceMesh1Q',
                         test_duration_hours: float = 24.0) -> Dict:
    """
    Valida coerência global da mesh 1Q em regime contínuo.
    """
    results = {
        'test_duration_hours': test_duration_hours,
        'phi_c_global_history': [],
        'cell_phi_c_distribution': [],
        'transport_error_stats': [],
        'scheduler_efficiency': []
    }

    # Executar carga de trabalho sintética representativa
    for hour in range(int(test_duration_hours)):
        # Gerar missão sintética com espectro de escalas realista
        mission = generate_synthetic_mission(
            complexity=1e6,  # 1 milhão de sub-tarefas
            scale_spectrum=torch.logspace(-1, 1, 100)  # escalas de 0.1 a 10
        )

        # Executar missão
        result = mesh.execute_mission(mission)

        # Coletar métricas
        results['phi_c_global_history'].append(
            result['integrated_phi_c']
        )

        # Amostrar Φ_C de células aleatórias
        sampled_cells = np.random.choice(
            list(mesh.cells.values()),
            size=100,
            replace=False
        )
        cell_phi_c = [
            cell.phi_c_monitor.get_current_spectrum().mean().item()
            for cell in sampled_cells
        ]
        results['cell_phi_c_distribution'].append({
            'mean': np.mean(cell_phi_c),
            'std': np.std(cell_phi_c),
            'min': np.min(cell_phi_c),
            'max': np.max(cell_phi_c)
        })

        # Coletar estatísticas de transporte
        transport_errors = []
        for task_result in result['execution_results'].values():
            if 'synchronization' in task_result:
                for sync_info in task_result['synchronization'].values():
                    transport_errors.append(
                        1.0 - sync_info['coherence_preserved']
                    )
        if transport_errors:
            results['transport_error_stats'].append({
                'mean_error': np.mean(transport_errors),
                'max_error': np.max(transport_errors)
            })

        # Eficiência do scheduler
        results['scheduler_efficiency'].append(
            result['cells_utilized'] / len(mesh.cells)
        )

        # Log progress
        if hour % 4 == 0:
            print(f"  Hour {hour+1}/{int(test_duration_hours)}: "
                  f"Φ_C global={result['integrated_phi_c']:.3f}, "
                  f"cells used={result['cells_utilized']}/{len(mesh.cells)}")

    # Analisar resultados
    analysis = {
        'phi_c_global_stable': np.std(results['phi_c_global_history']) < 0.02,
        'phi_c_global_mean': np.mean(results['phi_c_global_history']),
        'phi_c_global_min': np.min(results['phi_c_global_history']),
        'cell_phi_c_uniformity': np.mean([
            d['std'] for d in results['cell_phi_c_distribution']
        ]) < 0.05,
        'transport_error_acceptable': np.mean([
            s['mean_error'] for s in results['transport_error_stats']
        ]) < 0.01,
        'scheduler_efficiency': np.mean(results['scheduler_efficiency']) > 0.85
    }

    results['validation_passed'] = all(analysis.values())
    results['analysis'] = analysis

    return results
