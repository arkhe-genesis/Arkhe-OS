"""
websocket_bridge.py
"""
import asyncio, json, time, threading
from typing import Dict, Set, Any

try:
    from websockets.asyncio.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

class TelemetryWebSocketBridge:
    def __init__(self, orchestrator, host: str = "0.0.0.0", port: int = 9082):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.clients = set()
        self.running = False

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket: pass
        finally:
            self.clients.remove(websocket)

    async def broadcast_loop(self):
        while self.running:
            if self.clients:
                msg = json.dumps({"omega": self.orchestrator.field.get_network_omega(), "ts": time.time_ns()})
                for client in list(self.clients):
                    try: await client.send(msg)
                    except: pass
            await asyncio.sleep(0.5)

    def start(self):
        if not WEBSOCKETS_AVAILABLE: return
        self.running = True
        def run_async():
            async def main_loop():
                async with serve(self.handler, self.host, self.port):
                    print(f"✅ Bridge 3D ativo: ws://{self.host}:{self.port}")
                    await self.broadcast_loop()
            asyncio.run(main_loop())
        self.thread = threading.Thread(target=run_async, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
