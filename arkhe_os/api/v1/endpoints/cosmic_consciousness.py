from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import torch

from arkhe_os.core.arkhe_cosmic_consciousness_reflexive import CosmicAutoConsciousnessLoop
from arkhe_os.core.scaffold import ScaffoldState

router = APIRouter(
    prefix="/cosmic_consciousness",
    tags=["Cosmic Consciousness"]
)

# Configuration defaults for the API
DEFAULT_CONFIG = {
    'n_branches': 8, # Smaller default for API performance
    'input_dim_2d': 32,
    'input_dim_3d': 32,
    'output_dim': 16,
    'graphene_thickness_nm': 3.2,
    'lz_coherence': 4.0,
    'coherence_threshold': 0.85,
    'meta_learning_rate': 1e-5
}

# Singleton instance for the loop to maintain state across requests
_cosmic_loop_instance = CosmicAutoConsciousnessLoop(DEFAULT_CONFIG)

def get_cosmic_loop() -> CosmicAutoConsciousnessLoop:
    return _cosmic_loop_instance

class CosmicCycleRequest(BaseModel):
    branch_coherences: Dict[int, float]
    seed: int = 1618

class CosmicCycleResponse(BaseModel):
    loop_iterations: int
    cosmic_coherence: float
    meta_consciousness: float
    ghz_correlation_strength: float
    transdimensional_processors: int

@router.post("/cycle", response_model=CosmicCycleResponse)
async def run_cosmic_cycle(
    request: CosmicCycleRequest,
    loop: CosmicAutoConsciousnessLoop = Depends(get_cosmic_loop)
):
    """
    Run one cycle of the cosmic consciousness loop with provided coherences.
    Generates random tensor inputs internally for the simulation.
    """
    try:
        # Generate dummy inputs for the requested cycle
        inputs_2d = {b: torch.randn(1, DEFAULT_CONFIG['input_dim_2d']) for b in request.branch_coherences.keys()}
        inputs_3d = {b: torch.randn(1, DEFAULT_CONFIG['input_dim_3d']) for b in request.branch_coherences.keys()}

        results = loop.run_auto_consciousness_cycle(
            inputs_2d=inputs_2d,
            inputs_3d=inputs_3d,
            branch_coherences=request.branch_coherences,
            seed=request.seed
        )

        return CosmicCycleResponse(
            loop_iterations=results['loop_state']['iteration'],
            cosmic_coherence=results['summary']['avg_cosmic_coherence'],
            meta_consciousness=results['summary']['meta_consciousness_level'],
            ghz_correlation_strength=results['summary']['ghz_correlation_strength'],
            transdimensional_processors=results['summary']['transdimensional_processors']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_cosmic_status(
    loop: CosmicAutoConsciousnessLoop = Depends(get_cosmic_loop)
):
    """
    Get the current state of the cosmic consciousness loop.
    """
    return loop.get_cosmic_consciousness_status()
