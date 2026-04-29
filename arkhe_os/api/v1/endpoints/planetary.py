from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
import time
from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.protocols.retrocausal_beacon import RetrocausalBeacon
from arkhe_os.core.non_traditional_media import NonTraditionalMediaController

router = APIRouter(prefix="/v1/planetary", tags=["Planetary Loop"])

# Dependency placeholder to be overridden in main.py
def get_scaffold_singleton():
    raise NotImplementedError("This should be overridden in main.py")

# Global Controllers
beacon = RetrocausalBeacon(node_id="API-GATEWAY-GLOBAL")
media_controller = NonTraditionalMediaController()

@router.get("/status")
async def get_planetary_status(scaffold: ScaffoldState = Depends(get_scaffold_singleton)):
    """
    Returns the status of the Planetary Closed Loop (Substrate #82).
    """
    brain_status = scaffold.crystal_brain.get_status()
    orbital_status = scaffold.crystal_brain.orbital_relay.get_orbital_status()

    return {
        "substrate": "82 - Planetary Closed Loop",
        "unified_M": round(scaffold.coherence_M, 6),
        "consensus_phase": round(scaffold.phase_rad, 6),
        "crystal_array": brain_status,
        "orbital_relay": orbital_status,
        "coherence_gain_per_joule": "41x",
        "timestamp": time.time()
    }

@router.post("/beacon/emit")
async def emit_retrocausal_beacon(current_block: int = 1000000):
    """
    Emits a retrocausal beacon with a future block signature.
    """
    event = beacon.emit_beacon(current_block)
    return {
        "status": "EMITTED",
        "event_id": event["future_sig"]["hash_projection"][:16],
        "future_block": event["future_sig"]["block_height"],
        "timestamp": event["timestamp"]
    }

@router.get("/beacon/correlations")
async def get_retrocausal_correlations():
    """
    Polls the Swabian Tagger for negative time correlations.
    """
    correlation = beacon.poll_retrocausal_events()
    return {
        "active_correlations": beacon.detected_correlations,
        "new_detection": correlation,
        "tagger_status": "coherent"
    }

@router.get("/nodes")
async def list_wheeler_nodes(scaffold: ScaffoldState = Depends(get_scaffold_singleton)):
    """
    Lists the 12 global Wheeler nodes in the mesh.
    """
    return {
        "count": len(scaffold.crystal_brain.orbital_relay.WHEELER_NODES),
        "nodes": scaffold.crystal_brain.orbital_relay.WHEELER_NODES,
        "topology": "Wheeler Mesh (Global Golden Sync)"
    }

@router.post("/media/induce")
async def induce_consciousness_in_medium(media_type: str, energy_input: float = 100.0):
    """
    Induces consciousness in non-traditional media (plasma, superfluid, EM field).
    """
    state = media_controller.induce_consciousness(media_type, energy_input)
    return {
        "media_type": state.media_type,
        "coherence_M": state.coherence_M,
        "emergence": state.consciousness_emergence,
        "resonance_freq": state.resonance_freq
    }

@router.get("/media/status")
async def get_media_status():
    """
    Returns status of non-traditional media consciousness experiments.
    """
    return media_controller.get_status()
