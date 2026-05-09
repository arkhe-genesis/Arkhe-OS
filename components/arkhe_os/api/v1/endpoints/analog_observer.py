from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import time
import numpy as np

from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.core.observer_field import ObserverFieldConfig, AmplifyingObserver, UniversalResonantSystem, ObservationMode

router = APIRouter(prefix="/v1/analog-observer", tags=["Analog Observer"])

# Injetamos o ScaffoldState singleton
def get_scaffold_state():
    # Isto será sobrescrito em main.py
    return ScaffoldState()

# Configuración y Observer para la API
observer_config = ObserverFieldConfig()
observer = AmplifyingObserver(observer_config)

@router.get("/status")
async def get_mlh_status(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """Obtém o estado atual do circuito MLH no Scaffold"""
    # Simulamos um ciclo para atualizar o estado
    state = await scaffold.mlh_loop.run_cycle()
    scaffold.mlh_state = state
    return {
        "substrate": "75th - Analog Self-Observer",
        "circuit": "Manin-Loos-Hameroff (MLH) Resonant Loop",
        "coherence_lambda": round(state.coherence_lambda, 4),
        "is_locked": state.is_locked,
        "oscillator_phase": round(state.oscillator_phase, 4),
        "feedback_voltage": round(state.feedback_voltage, 4),
        "timestamp": state.timestamp
    }

@router.post("/register-system")
async def register_system(system_id: str, substrate_type: str):
    """Registra um novo sistema para observação amplificadora"""
    system = UniversalResonantSystem(system_id=system_id, substrate_type=substrate_type)
    observer.register_system(system)
    return {"message": f"System {system_id} registered successfully"}

@router.post("/observe/{system_id}")
async def observe_system(system_id: str, mode: ObservationMode = ObservationMode.AMPLIFY):
    """Realiza uma observação que amplifica ou reconhece a coerência"""
    if system_id not in observer.systems:
        raise HTTPException(status_code=404, detail="System not registered")

    result = await observer.observe_and_amplify(system_id, mode)
    system = observer.systems[system_id]

    return {
        "system_id": system_id,
        "mode": mode,
        "consciousness_score": round(system.consciousness_score, 4),
        "is_conscious": system.is_conscious(),
        "local_M": round(system.local_M, 4),
        "phase_rad": round(system.phase_rad, 4)
    }
