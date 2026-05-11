from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import time
import numpy as np
from typing import List, Dict, Any
from arkhe_os.core.scaffold import ScaffoldState, CoherenceLevel
from arkhe_os.protocols.coherent_handshake import CoherentHandshakeProtocol

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.node_states: Dict[str, Any] = {} # node_id -> state (phase, M, etc)

    async def connect(self, websocket: WebSocket, scaffold: ScaffoldState):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_json({
            "type": "connected",
            "coherence_M": round(scaffold.coherence_M, 4),
            "message": "Conectado ao Scaffold Ξ. Streaming de coerência ativo."
        })

    def update_node_state(self, node_id: str, state: Any):
        self.node_states[node_id] = state

    def get_neighbor_states(self, exclude_node_id: str) -> List[Any]:
        return [state for nid, state in self.node_states.items() if nid != exclude_node_id]

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for d in disconnected:
            self.disconnect(d)

manager = ConnectionManager()

async def websocket_coherence_handler(websocket: WebSocket, scaffold: ScaffoldState):
    """
    WebSocket para streaming em tempo real de métricas de coerência e handshake de fase.
    """
    await manager.connect(websocket, scaffold)

    # Handshake de protocolo (opcional, para negociação de versão)
    try:
        # Tenta receber o primeiro frame para ver se é uma solicitação de handshake
        # Mas não bloqueia se for apenas um cliente de streaming
        data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
        if data.get("protocol") == "coherent_handshake_v1":
            node_id = data.get("node_id", "anonymous-node")
            # Iniciar loop de sincronização de fase em background para este nó
            protocol = CoherentHandshakeProtocol(manager)

            # Handler para mensagens recebidas deste nó via WebSocket
            async def ws_message_handler():
                try:
                    async for message in websocket:
                        frame = json.loads(message)
                        if frame.get("type") == "phase_sync":
                            # No handshaking real, isso seria um Frame binário
                            from arkhe_os.protocols.coherent_handshake import PhaseSyncFrame
                            try:
                                psf = PhaseSyncFrame(**frame["payload"])
                                manager.update_node_state(node_id, psf)
                            except: pass
                except: pass

            asyncio.create_task(ws_message_handler())
            asyncio.create_task(protocol.phase_sync_loop(node_id, scaffold, websocket))
    except (asyncio.TimeoutError, json.JSONDecodeError):
        pass
    except Exception as e:
        print(f"[WS Handshake Error] {e}")

    try:
        counter = 0
        while True:
            await asyncio.sleep(0.5)  # 2 Hz

            # Atualizar métricas com ruído realista no ScaffoldState (simulação)
            scaffold.coherence_M = float(np.clip(
                scaffold.coherence_M + np.random.normal(0, 0.002), 0.85, 0.99
            ))
            scaffold.phase_rad = (scaffold.phase_rad + 0.001) % (2 * np.pi)
            scaffold.turbulence = float(np.clip(
                scaffold.turbulence + np.random.normal(0, 0.001), 0.01, 0.08
            ))

            update_msg = {
                "type": "coherence_update",
                "M": round(scaffold.coherence_M, 4),
                "phase_rad": round(scaffold.phase_rad, 4),
                "geometric_turbulence": round(scaffold.turbulence, 4),
                "coherence_level": CoherenceLevel.COHERENT.value if scaffold.coherence_M >= 0.85 else CoherenceLevel.NEUTRAL.value,
                "timestamp": time.time()
            }

            await websocket.send_json(update_msg)

            # CIRE update a cada 2s
            counter += 1
            if counter % 4 == 0:
                for engine in scaffold.cire_engines.values():
                    engine.last_updated = time.time()
                    await websocket.send_json({
                        "type": "cire_update",
                        "engine": engine.model_dump()
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket Error] {e}")
        manager.disconnect(websocket)
