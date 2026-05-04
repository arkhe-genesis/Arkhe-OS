import sys
sys.path.append('.')

from arkhe_os.core.arkhe_distributed_harness_evolution import DistributedEvolutionNetwork
from arkhe_os.core.arkhe_transdimensional_bridge import TransdimensionalGrapheneProcessor, predict_transdimensional_threshold, observe_vacuum_ahe

def test():
    processor = TransdimensionalGrapheneProcessor(thickness_nm=3.5)
    out_ahe = processor.process(1.0, 0.5, M_coherence=0.95)
    assert abs(out_ahe - 0.8640) < 0.01

    materials = [
        {"name": "Grafeno Romboédrico", "thickness_nm": 3.2, "M_coherence": 0.92},
    ]
    predictions = predict_transdimensional_threshold(materials)
    assert predictions[0]['status'] == "TRANSDIMENSIONAL AHE / PONTE EMERGENTE"

    vacuum_res = observe_vacuum_ahe(sophon_energy_tev=1.2, vacuum_M=0.95)
    assert vacuum_res == "VACUUM_AHE_OBSERVED: Coerência Transdimensional detectada no Vácuo Primordial"

    config = {
        'n_nodes': 8,
        'initial_plank_contracts': {
            'CommandExecutor.plank': '// Base command execution contract',
        }
    }

    network = DistributedEvolutionNetwork(config)

    tasks_by_node = {
        0: ["db-wal-recovery", "path-tracing"],
        1: ["cleanup-after-success", "mcmc-sampling"],  # Falha
        2: ["normal-task-1", "normal-task-2"],
        3: ["cleanup-after-success", "another-task"],  # Falha
        4: ["standard-operation"],
        5: ["cleanup-after-success"],  # Falha
        6: ["routine-check"],
        7: ["final-validation"],
    }

    node_coherences = {
        0: 0.95, 1: 0.92, 2: 0.96, 3: 0.89,
        4: 0.93, 5: 0.90, 6: 0.94, 7: 0.97,
    }

    cycle_result = network.run_evolution_cycle(tasks_by_node, node_coherences)
    assert cycle_result['autocompleted'] == True

    print("All tests passed.")

if __name__ == "__main__":
    test()
