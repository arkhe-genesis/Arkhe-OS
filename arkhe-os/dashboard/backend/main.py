from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio, json, time, random, math
from collections import defaultdict

app = FastAPI(title="ARKHE OS Dashboard", version="inf.omega")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.event_history = defaultdict(list)
        self.max_history = 1000

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                pass

    def add_event(self, event: dict):
        self.event_history[event["classification"]].append(event)
        if len(self.event_history[event["classification"]]) > self.max_history:
            self.event_history[event["classification"]].pop(0)

manager = ConnectionManager()

def generate_event() -> dict:
    """Simula um evento de particula realista."""
    particle = random.choices(
        ["alpha", "beta_gamma", "muon", "noise"],
        weights=[0.05, 0.15, 0.10, 0.70]
    )[0]

    if particle == "alpha":
        amplitude = random.gauss(1500, 200)
        width = random.gauss(8, 2)
    elif particle == "beta_gamma":
        amplitude = random.gauss(400, 80)
        width = random.gauss(25, 10)
    elif particle == "muon":
        amplitude = random.gauss(600, 100)
        width = random.gauss(60, 15)
    else:
        amplitude = random.gauss(20, 10)
        width = random.gauss(5, 3)

    return {
        "timestamp": int(time.time() * 1e9),
        "channel": random.randint(0, 127),
        "amplitude_mV": max(0, round(amplitude, 1)),
        "integral_nVs": max(0, round(amplitude * width * 0.5, 1)),
        "width_ns": max(1, round(width, 1)),
        "classification": particle,
        "confidence": round(random.uniform(0.85, 0.99), 3),
        "array_sector": random.choice(["N", "S", "E", "W", "C"])
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
    <head><title>ARKHE OS Dashboard</title></head>
    <body>
        <h1>ARKHE OS - Particle Detection Dashboard</h1>
        <p>WebSocket endpoint: <code>ws://localhost:8000/ws</code></p>
        <pre id="events"></pre>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = (e) => {
                const event = JSON.parse(e.data);
                document.getElementById("events").textContent +=
                    JSON.stringify(event, null, 2) + "\\n";
            };
        </script>
    </body>
    </html>
    """

@app.get("/api/status")
async def status():
    return {
        "server": "ARKHE OS Dashboard",
        "version": "inf.omega",
        "active_connections": len(manager.active_connections),
        "event_counts": {
            k: len(v) for k, v in manager.event_history.items()
        }
    }

@app.get("/api/events/summary")
async def event_summary():
    return {
        "total_events": sum(len(v) for v in manager.event_history.values()),
        "by_classification": {
            k: len(v) for k, v in manager.event_history.items()
        },
        "latest_events": [
            manager.event_history[k][-1]
            for k in manager.event_history
            if manager.event_history[k]
        ][-5:]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            event = generate_event()
            manager.add_event(event)
            await manager.broadcast(event)
            await asyncio.sleep(random.uniform(0.1, 1.0))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)