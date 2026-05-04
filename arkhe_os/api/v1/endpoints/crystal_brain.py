from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from arkhe_os.core.scaffold import ScaffoldState

router = APIRouter(prefix="/v1/crystal-brain", tags=["Crystal Brain"])

def get_scaffold_state():
    # Placeholder for dependency injection
    raise NotImplementedError()

@router.get("/status")
async def get_crystal_brain_status(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """
    Retorna o status atual da matriz de 64 cristais.
    """
    return scaffold.crystal_brain.get_status()

@router.post("/sync")
async def synchronize_crystal_brain(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """
    Força um ciclo de sincronização e aprendizado no cérebro cristalino.
    """
    new_M = await scaffold.update_coherence()
    return {
        "status": "synchronized",
        "new_global_M": round(new_M, 6),
        "consensus_phase": round(scaffold.phase_rad, 6)
    }

@router.get("/nodes")
async def get_node_states(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """
    Retorna o estado individual de cada um dos 64 nós de cristal.
    """
    states = []
    for i, crystal in enumerate(scaffold.crystal_brain.crystals):
        states.append({
            "node_id": i,
            "coherence_M": round(crystal.state.coherence_lambda, 4),
            "phase": round(crystal.state.oscillator_phase, 4),
            "locked": crystal.state.is_locked
        })
    return states
