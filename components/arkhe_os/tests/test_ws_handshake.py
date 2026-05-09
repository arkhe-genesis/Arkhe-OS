import asyncio
import websockets
import json
import time
import pytest

@pytest.mark.asyncio
async def test_ws_handshake():
    uri = "ws://localhost:8000/ws/coherence"
    async with websockets.connect(uri) as websocket:
        # 1. Receive initial connection message
        resp = await websocket.recv()
        data = json.loads(resp)
        assert data['type'] == 'connected'

        # 2. Initiate coherent handshake
        handshake_msg = {
            "protocol": "coherent_handshake_v1",
            "node_id": "test-node-01"
        }
        await websocket.send(json.dumps(handshake_msg))

        # 3. Receive updates and filter for coherence_update
        updates_received = 0
        timeout = time.time() + 10
        while updates_received < 1 and time.time() < timeout:
            resp = await websocket.recv()
            data = json.loads(resp)
            if data['type'] == 'coherence_update':
                updates_received += 1

        assert updates_received >= 1
