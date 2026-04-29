import asyncio
import time
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from arkhe_os.core.scaffold import ScaffoldState

class PhaseSyncFrame(BaseModel):
    node_id: str
    local_phase_rad: float
    local_M: float
    geometric_turbulence: float
    reference_branch: str
    confidence: float
    timestamp_ns: int

    def validate(self):
        return True

    def to_binary(self):
        # Em produção: serialização binária real (Header + Payload + Footer)
        import json
        return json.dumps(self.model_dump()).encode()

    @classmethod
    def from_binary(cls, data: bytes):
        import json
        return cls(**json.loads(data.decode()))

class CoherentHandshakeProtocol:
    """Protocolo de handshake para sincronização de fase entre nós da Malha"""

    PHASE_SYNC_INTERVAL_S = 0.1  # 10 Hz update rate
    PHASE_TOLERANCE_RAD = 0.01   # Tolerância para considerar "sincronizado"

    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager

    async def measure_local_phase(self, scaffold_state: ScaffoldState) -> float:
        # Simula medição do hardware (ex: Swabian Tagger)
        return scaffold_state.phase_rad

    async def adjust_local_oscillator(self, scaffold_state: ScaffoldState, adjustment: float):
        # Ajusta fase no estado global
        scaffold_state.phase_rad = (scaffold_state.phase_rad + adjustment) % (2 * np.pi)

    async def phase_sync_loop(self, local_node_id: str, scaffold_state: ScaffoldState, websocket=None):
        """Loop principal de sincronização de fase"""
        while True:
            # 1. Medir fase local e coerência
            local_phase = await self.measure_local_phase(scaffold_state)
            local_M = scaffold_state.coherence_M

            # 2. Construir frame de sincronização
            frame = PhaseSyncFrame(
                node_id=local_node_id,
                local_phase_rad=local_phase,
                local_M=local_M,
                geometric_turbulence=scaffold_state.turbulence,
                reference_branch=scaffold_state.active_branches[0].branch_id,
                confidence=0.95,
                timestamp_ns=time.time_ns()
            )

            # 3. Broadcast para nós vizinhos
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "phase_sync",
                    "payload": frame.model_dump()
                })

            # 4. Coletar respostas (em produção: via websocket)
            # Para o simulador, os vizinhos são gerenciados pelo ScaffoldState ou WebSocketManager
            neighbor_phases = await self.collect_neighbor_phases(websocket)

            if neighbor_phases:
                # Média ponderada por coerência dos vizinhos
                weights = [p.confidence * p.local_M for p in neighbor_phases]
                mesh_phase = np.average([p.local_phase_rad for p in neighbor_phases], weights=weights)

                # 5. Ajustar oscilador local para minimizar Δφ
                phase_error = mesh_phase - local_phase
                # Wrap phase error to [-pi, pi]
                phase_error = (phase_error + np.pi) % (2 * np.pi) - np.pi

                if abs(phase_error) > self.PHASE_TOLERANCE_RAD:
                    await self.adjust_local_oscillator(scaffold_state, phase_error * 0.1)  # Ganho conservador

            await asyncio.sleep(self.PHASE_SYNC_INTERVAL_S)

     async def collect_neighbor_phases(self, websocket, local_node_id: Optional[str] = None) -> List[PhaseSyncFrame]:
        """Coleta frames de sincronização de nós vizinhos"""
        if self.websocket_manager:
            # Filtra o próprio nó para evitar amortecimento do consenso
            return self.websocket_manager.get_neighbor_states(exclude_node_id=local_node_id)
        return []
