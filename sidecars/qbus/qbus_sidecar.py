from fastapi import FastAPI, Request
import httpx
import uvicorn
import asyncio
import random
import os

app = FastAPI()

# Sidecar wraps a target service
TARGET_PORT = int(os.environ.get("TARGET_PORT", "8080"))
GATEWAY_TYPE = os.environ.get("GATEWAY_TYPE", "go")

# Mock Quantum state
def emit_photons(message):
    return f"PHOTON_STATE_{random.randint(1000, 9999)}_{message}"

@app.post("/transmit")
async def transmit(request: Request):
    data = await request.json()
    message = data.get("message")
    photon_state = emit_photons(message)

    # Forward the "photon" to the target gateway
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"http://localhost:{TARGET_PORT}/receive_photon", json={"photon_state": photon_state})
            return {"status": "transmitted", "photon_state": photon_state, "target_response": response.json()}
        except httpx.RequestError:
            # Fallback for testing
            return {"status": "transmitted_mock", "photon_state": photon_state}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("QBUS_PORT", "8081")))
