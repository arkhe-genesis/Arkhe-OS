from fastapi import APIRouter, HTTPException, Depends
from arkhe_os.orchestration.collective_resonance_v4_2 import ProductionResonanceCoordinator
from arkhe_os.core.scaffold import ScaffoldState
import numpy as np

router = APIRouter(prefix="/v1/resonance", tags=["Resonance"])

# In production, this would be injected
def get_scaffold_state():
    raise NotImplementedError()

@router.post("/production/run")
async def run_production_resonance(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """
    Inicia uma sessão de ressonância de produção v∞.4.2.
    """
    try:
        coordinator = ProductionResonanceCoordinator()

        # Mapear agentes do scaffold
        agent_configs = []
        for i in range(12):
            agent_configs.append({
                "agent_id": f"CREW-{i+1:02d}",
                "role": "crew",
                "local_phase_rad": np.random.uniform(0, 2*np.pi),
                "local_M": 0.88 + np.random.uniform(0, 0.06),
                "websocket_uri": f"ws://node-{i:02d}.local"
            })
        agent_configs.append({"agent_id": "AGI-PRIME", "role": "agi", "local_phase_rad": 0.0, "local_M": 0.94, "websocket_uri": ""})
        agent_configs.append({"agent_id": "AGI-SEC", "role": "agi", "local_phase_rad": 0.0, "local_M": 0.92, "websocket_uri": ""})
        agent_configs.append({"agent_id": "ARCHITECT", "role": "architect", "local_phase_rad": 1.618, "local_M": 0.96, "websocket_uri": ""})

        await coordinator.initialize(agent_configs)
        result = await coordinator.run_production_session()

        # Atualizar scaffold real com ganho obtido
        scaffold.coherence_M = min(1.0, scaffold.coherence_M + result["delta_M"])

        return {
            "status": "success",
            "metrics": result,
            "updated_scaffold_M": round(scaffold.coherence_M, 4)
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
