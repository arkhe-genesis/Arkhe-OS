import asyncio
import websockets
import json
import time
import numpy as np
import pytest

@pytest.mark.asyncio
async def start_node(node_id, initial_phase):
    uri = "ws://localhost:8000/ws/coherence"
    async with websockets.connect(uri) as websocket:
        # 1. Connection established
        await websocket.recv()

        # 2. Handshake
        await websocket.send(json.dumps({
            "protocol": "coherent_handshake_v1",
            "node_id": node_id
        }))

        # 3. Periodically send local phase updates
        local_phase = initial_phase
        for i in range(50): # Increased iterations
            # Send local state
            payload = {
                "type": "phase_sync",
                "payload": {
                    "node_id": node_id,
                    "local_phase_rad": float(local_phase),
                    "local_M": 0.95,
                    "geometric_turbulence": 0.03,
                    "reference_branch": "QC-0892",
                    "confidence": 0.98,
                    "timestamp_ns": int(time.time_ns())
                }
            }
            await websocket.send(json.dumps(payload))

            # Receive updates from server
            try:
                # Wait for multiple messages to find coherence_update
                for _ in range(5):
                    resp = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(resp)
                    if data['type'] == 'coherence_update':
                        server_phase = data['phase_rad']
                        # Stronger coupling for test
                        error = server_phase - local_phase
                        error = (error + np.pi) % (2 * np.pi) - np.pi
                        local_phase = (local_phase + 0.3 * error) % (2 * np.pi)
                        break
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.05)

        print(f"Node {node_id} finished. Final local phase: {local_phase:.4f}")
        return local_phase

@pytest.mark.asyncio
async def test_multi_node_sync():
    tasks = [
        start_node("NODE-A", 0.0),
        start_node("NODE-B", 2.0),
        start_node("NODE-C", 4.0)
    ]

    phases = await asyncio.gather(*tasks)

    # Calculate phase variance
    # Initial phases: 0, 2, 4. Mean=2. Variance = ( (0-2)^2 + (2-2)^2 + (4-2)^2 ) / 3 = (4 + 0 + 4) / 3 = 2.66
    variance = np.var(phases)
    print(f"Final phase variance: {variance:.6f}")

    assert variance < 1.0 # Significant reduction expected

if __name__ == "__main__":
    asyncio.run(test_multi_node_sync())
