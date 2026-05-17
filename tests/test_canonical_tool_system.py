import pytest
import asyncio
import uuid
from tool_calling.canonical_tool_system import (
    CanonicalToolCallingSystem,
    ToolDefinition,
    ToolCallRequest,
    ToolCallStatus
)

@pytest.fixture
def tool_system():
    return CanonicalToolCallingSystem()

def test_tool_registration(tool_system):
    def dummy_handler(params):
        return params

    tool = ToolDefinition(
        tool_id="test_tool",
        name="Test Tool",
        description="A tool for testing.",
        parameters_schema={"type": "object"},
        handler=dummy_handler,
        agent_owner="agent_1"
    )

    tool_system.register_tool(tool)
    assert "test_tool" in tool_system.tool_registry
    assert "test_tool" in tool_system.circuit_breakers

@pytest.mark.asyncio
async def test_tool_invocation_success(tool_system):
    def dummy_handler(params):
        return {"success": True, "input": params}

    tool = ToolDefinition(
        tool_id="test_tool",
        name="Test Tool",
        description="A tool for testing.",
        parameters_schema={"type": "object"},
        handler=dummy_handler,
        agent_owner="agent_1"
    )
    tool_system.register_tool(tool)

    request = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="test_tool",
        parameters={"key": "value"},
        agent_id="agent_1"
    )

    result = await tool_system.invoke_tool(request)
    assert result.status == ToolCallStatus.SUCCESS
    assert result.result["success"] is True
    assert result.result["input"] == {"key": "value"}

@pytest.mark.asyncio
async def test_idempotent_tool_invocation(tool_system):
    call_count = 0
    def side_effect_handler(params):
        nonlocal call_count
        call_count += 1
        return {"count": call_count}

    tool = ToolDefinition(
        tool_id="idempotent_tool",
        name="Idempotent Tool",
        description="A tool for testing idempotency.",
        parameters_schema={"type": "object"},
        handler=side_effect_handler,
        agent_owner="agent_1",
        idempotent=True
    )
    tool_system.register_tool(tool)

    idempotency_key = "unique_key_123"

    request1 = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="idempotent_tool",
        parameters={"key": "value"},
        agent_id="agent_1",
        idempotency_key=idempotency_key
    )

    result1 = await tool_system.invoke_tool(request1)
    assert result1.status == ToolCallStatus.SUCCESS
    assert result1.result["count"] == 1
    assert call_count == 1

    request2 = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="idempotent_tool",
        parameters={"key": "value"},
        agent_id="agent_1",
        idempotency_key=idempotency_key
    )

    result2 = await tool_system.invoke_tool(request2)
    assert result2.status == ToolCallStatus.SUCCESS
    assert result2.result["count"] == 1  # Should return the cached result
    assert call_count == 1  # Handler should not be called again

@pytest.mark.asyncio
async def test_circuit_breaker(tool_system):
    def failing_handler(params):
        raise ValueError("Simulated failure")

    tool = ToolDefinition(
        tool_id="failing_tool",
        name="Failing Tool",
        description="A tool that always fails.",
        parameters_schema={"type": "object"},
        handler=failing_handler,
        agent_owner="agent_1",
        failure_threshold=2
    )
    tool_system.register_tool(tool)

    # First call - fails
    request1 = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="failing_tool",
        parameters={},
        agent_id="agent_1"
    )
    result1 = await tool_system.invoke_tool(request1)
    assert result1.status == ToolCallStatus.FAILED

    # Second call - fails and trips breaker
    request2 = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="failing_tool",
        parameters={},
        agent_id="agent_1"
    )
    result2 = await tool_system.invoke_tool(request2)
    assert result2.status == ToolCallStatus.DEAD_LETTER # circuit breaker opens

    # Third call - circuit breaker is open
    request3 = ToolCallRequest(
        call_id=str(uuid.uuid4()),
        tool_id="failing_tool",
        parameters={},
        agent_id="agent_1"
    )
    result3 = await tool_system.invoke_tool(request3)
    assert result3.status == ToolCallStatus.CIRCUIT_OPEN
