import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Dict

class MockTemporalChain:
    async def anchor_event(self, event_type: str, payload: dict) -> dict:
        return {"seal": f"mock_seal_{int(time.time())}"}

class MockCanonicalToolCallingSystem:
    def __init__(self):
        self.registered_tools = []

    def register_tool(self, tool):
        self.registered_tools.append(tool)

import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock

from moonpay.moonpay_canonical_tool import (
    MoonPayCanonicalTool, MoonPayConfig, MoonPayEnvironment, MoonPayApiResponse
)

@pytest.fixture
def config():
    return MoonPayConfig(
        api_key="sk_test_mock",
        webhook_key="whsec_mock",
        environment=MoonPayEnvironment.SANDBOX
    )

@pytest.fixture
def temporal():
    return MockTemporalChain()

@pytest.fixture
def tool_system():
    return MockCanonicalToolCallingSystem()

@pytest.fixture
def moonpay(config, tool_system, temporal):
    return MoonPayCanonicalTool(
        config=config,
        tool_system=tool_system,
        temporal_chain=temporal
    )

@pytest.mark.asyncio
async def test_moonpay_create_session(moonpay):
    # Mock the HTTP session
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.headers = {"X-Request-Id": "req_123"}
    mock_resp.json.return_value = {"token": "sess_123"}

    mock_session = MagicMock()

    mock_req_ctx = AsyncMock()
    mock_req_ctx.__aenter__.return_value = mock_resp
    mock_session.request.return_value = mock_req_ctx

    # fix the issue where AsyncMock doesn't support async context manager by default
    # https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock
    # To get around this we can just use MagicMock where we implement the async protocol
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc, tb):
            pass
    mock_session.request.return_value = AsyncContextManager()

    moonpay._session = mock_session

    params = {
        "external_customer_id": "cust_123",
        "device_ip": "1.2.3.4",
        "email": "test@example.com"
    }

    res = await moonpay.create_session(**params)

    assert res.status_code == 200
    assert res.data["token"] == "sess_123"
    assert res.temporal_seal.startswith("mock_seal_")

    # Check if correct request was made
    mock_session.request.assert_called_once_with(
        "POST",
        "https://api.moonpay.dev/platform/v1/sessions",
        json={"externalCustomerId": "cust_123", "deviceIp": "1.2.3.4", "email": "test@example.com"},
        headers={"Content-Type": "application/json", "Authorization": "Api-Key sk_test_mock"},
        timeout=aiohttp.ClientTimeout(total=15)
    )

@pytest.mark.asyncio
async def test_moonpay_get_transaction(moonpay):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.headers = {"X-Request-Id": "req_456"}
    mock_resp.json.return_value = {"id": "tx_456", "status": "completed"}

    mock_session = MagicMock()

    mock_req_ctx = AsyncMock()
    mock_req_ctx.__aenter__.return_value = mock_resp
    mock_session.request.return_value = mock_req_ctx

    # fix the issue where AsyncMock doesn't support async context manager by default
    # https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock
    # To get around this we can just use MagicMock where we implement the async protocol
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc, tb):
            pass
    mock_session.request.return_value = AsyncContextManager()

    moonpay._session = mock_session

    res = await moonpay.get_transaction("tx_456")

    assert res.status_code == 200
    assert res.data["id"] == "tx_456"

    mock_session.request.assert_called_once_with(
        "GET",
        "https://api.moonpay.dev/platform/v1/transactions/tx_456",
        json=None,
        headers={"Content-Type": "application/json", "Authorization": "Api-Key sk_test_mock"},
        timeout=aiohttp.ClientTimeout(total=15)
    )

def test_verify_webhook(moonpay):
    payload = b'{"type":"transaction_updated","data":{"id":"tx_123"}}'
    import hmac, hashlib
    valid_signature = hmac.new(b"whsec_mock", payload, hashlib.sha256).hexdigest()

    assert moonpay.verify_webhook_signature(payload, valid_signature) == True
    assert moonpay.verify_webhook_signature(payload, "invalid") == False

def test_register_tools(moonpay, tool_system):
    count = moonpay.register_all_tools(tool_system)
    assert count == 6
    assert len(tool_system.registered_tools) == 6

    tool_names = [t.tool_id for t in tool_system.registered_tools]
    assert "moonpay_create_session" in tool_names
    assert "moonpay_get_quote" in tool_names
