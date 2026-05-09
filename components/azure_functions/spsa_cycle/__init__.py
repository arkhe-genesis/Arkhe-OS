import azure.functions as func
import numpy as np
import json
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos arkhe_os e scripts
sys.path.append(str(Path(__file__).parent.parent.parent))

from arkhe_os.core.crystal_brain import CrystalBrainArray
from scripts.arkhe_homeostasis_v327_1.expanded_parameter_space import multi_objective_score

def run_ising_pipeline_mock(phases, threshold):
    """Mock until run_ising_pipeline is fully accessible."""
    return {
        'capture_fraction': 0.85,
        'community_details': {
            0: {'regime': 'CAPTURE', 'manifold_dim': 3, 'rho': 0.9}
        },
        'regime_distribution': {'CAPTURE': 1}
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function que executa um ciclo de otimização SPSA sob demanda."""
    kappa = float(req.params.get('kappa', 0.75))
    lambda_l1 = float(req.params.get('lambda_l1', 0.02))

    # Executar simulação e classificação Ising (vetorizado com NumPy)
    cb = CrystalBrainArray()
    # Assuming cb can generate phases or we use a mock for now
    phases = np.random.uniform(0, 2*np.pi, (300, 768))

    # ir = run_ising_pipeline(phases, threshold=lambda_l1)
    ir = run_ising_pipeline_mock(phases, threshold=lambda_l1)

    score = multi_objective_score(ir)

    return func.HttpResponse(
        json.dumps({"score": score, "regime": ir['regime_distribution']}),
        mimetype="application/json"
    )
