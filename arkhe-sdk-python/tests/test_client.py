import pytest
import asyncio
from aiohttp import web
from arkhe_sdk.services.client import ArkheClient
from arkhe_sdk.models.coherence import ValidationRequest, HealthResponse

async def mock_health_handler(request):
    return web.json_response({
        "status": "ready",
        "version": "1.0.0",
        "global_phi_c": 0.95,
        "substrates": {},
        "mrc_status": {"status": "operational"}
    })

async def mock_validation_handler(request):
    data = await request.json()
    return web.json_response({
        "validation_id": "test_hash_123",
        "status": "queued",
        "estimated_completion_seconds": 30
    })

@pytest.fixture
async def cli(aiohttp_client):
    app = web.Application()
    app.router.add_get('/health/ready', mock_health_handler)
    app.router.add_post('/v1/validations/submit', mock_validation_handler)
    return await aiohttp_client(app)

@pytest.mark.asyncio
async def test_get_health(cli):
    # Setup test server URL
    endpoint = f"http://{cli.host}:{cli.port}"

    async with ArkheClient(endpoint, "fake_token") as client:
        # Check health
        health = await client.get_health()
        assert health.status == "ready"
        assert health.global_phi_c == 0.95

@pytest.mark.asyncio
async def test_submit_validation(cli):
    endpoint = f"http://{cli.host}:{cli.port}"

    async with ArkheClient(endpoint, "fake_token") as client:
        request = ValidationRequest(
            experiment_type="quantum_simulation",
            material="herbertsmithite",
            data_hash="abc123hash",
            cves=["CVE-2023-1234"],
            meta={"notes": "initial test"}
        )
        response = await client.submit_validation(request)
        assert response["validation_id"] == "test_hash_123"
        assert response["status"] == "queued"
