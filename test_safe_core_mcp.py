import pytest
import json
import asyncio
from safe_core_mcp.server import ArkheMCPServer

@pytest.fixture
def mcp_server():
    return ArkheMCPServer()

@pytest.mark.asyncio
async def test_initialize(mcp_server):
    req = {
        "method": "initialize",
        "params": {},
        "id": 1
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "SafeCore-MCP"
    assert "tools" in resp["result"]["capabilities"]

@pytest.mark.asyncio
async def test_tools_list(mcp_server):
    req = {
        "method": "tools/list",
        "id": 2
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 2
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "scan_code" in tool_names
    assert "phi_c_status" in tool_names

@pytest.mark.asyncio
async def test_tools_call(mcp_server):
    req = {
        "method": "tools/call",
        "params": {
            "name": "phi_c_status",
            "arguments": {}
        },
        "id": 3
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 3
    content = json.loads(resp["result"]["content"][0]["text"])
    assert "coherence" in content

@pytest.mark.asyncio
async def test_resources_list(mcp_server):
    req = {
        "method": "resources/list",
        "id": 4
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 4
    resources = resp["result"]["resources"]
    uris = [r["uri"] for r in resources]
    assert "arkhe://metrics/phi_c" in uris

@pytest.mark.asyncio
async def test_resources_read(mcp_server):
    req = {
        "method": "resources/read",
        "params": {
            "uri": "arkhe://metrics/phi_c"
        },
        "id": 5
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 5
    content = json.loads(resp["result"]["contents"][0]["text"])
    assert "coherence" in content

@pytest.mark.asyncio
async def test_prompts_list(mcp_server):
    req = {
        "method": "prompts/list",
        "id": 6
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 6
    prompts = resp["result"]["prompts"]
    names = [p["name"] for p in prompts]
    assert "security_audit" in names

@pytest.mark.asyncio
async def test_prompts_get(mcp_server):
    req = {
        "method": "prompts/get",
        "params": {
            "name": "security_audit"
        },
        "id": 7
    }
    resp = await mcp_server.handle_request(req)
    assert resp["id"] == 7
    messages = resp["result"]["messages"]
    assert len(messages) > 0
