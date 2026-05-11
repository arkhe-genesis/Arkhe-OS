import aiohttp
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from ..models.coherence import HealthResponse, ValidationRequest, CoherenceMetrics
import json

class ArkheClient:
    def __init__(self, endpoint: str, auth_token: str):
        self.endpoint = endpoint
        self.auth_token = auth_token
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            base_url=self.endpoint,
            headers={
                "User-Agent": "ARKHE-SDK/1.0",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def get_health(self) -> HealthResponse:
        async with self._session.get("/health/ready") as resp:
            resp.raise_for_status()
            data = await resp.json()
            return HealthResponse(**data)

    async def submit_validation(self, request: ValidationRequest) -> Dict[str, Any]:
        async with self._session.post("/v1/validations/submit", json=request.model_dump()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def stream_coherence(self):
        parsed_url = urlparse(self.endpoint)
        scheme = "wss" if parsed_url.scheme == "https" else "ws"
        ws_url = parsed_url._replace(scheme=scheme).geturl() + "/ws/coherence/stream"

        async with self._session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield json.loads(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
