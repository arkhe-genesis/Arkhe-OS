import pytest
import asyncio
from substrato_181_agentic_architecture import (
    MockTemporalChain,
    ArkheAgent,
    ToolSpec,
    ToolPermission,
    GuardResult,
    ExecutionContext,
    Plan,
    GuardrailsEnforcer,
    MultiAgentOrchestrator,
    TaskSpec
)

@pytest.fixture
def tc():
    return MockTemporalChain()

@pytest.mark.asyncio
async def test_agent_creation(tc):
    agent = ArkheAgent(agent_id="test-agent", agent_type="Test", version="1.0", tc=tc)
    assert agent.agent_id == "test-agent"
    assert agent.phi_c == 0.99

@pytest.mark.asyncio
async def test_guardrails_static(tc):
    guard = GuardrailsEnforcer(tc)
    context = ExecutionContext(agent_phi_c=0.99)
    plan = Plan(action="execute", params={"cmd": "rm -rf /"}, risk_level=5, requires_consensus=False)
    result = await guard.validate(plan, context)
    assert result.blocked is True
    assert result.reason == "static_rule"

@pytest.mark.asyncio
async def test_guardrails_dynamic(tc):
    guard = GuardrailsEnforcer(tc)
    context = ExecutionContext(agent_phi_c=0.8) # Low phi_c
    plan = Plan(action="dangerous_action", params={}, risk_level=3, requires_consensus=False)
    result = await guard.validate(plan, context)
    assert result.blocked is True
    assert result.reason == "phi_c_low"

@pytest.mark.asyncio
async def test_tool_use(tc):
    agent = ArkheAgent(agent_id="test-agent", agent_type="Test", version="1.0", tc=tc)

    async def dummy_handler(params):
        return {"status": "success", "val": params.get("val")}

    tool = ToolSpec(
        name="dummy_tool",
        description="A dummy tool",
        parameters_schema={},
        permission=ToolPermission.READ_ONLY,
        handler=dummy_handler,
        risk_level=1
    )
    agent.toolset.register(tool)

    plan = Plan(action="dummy_tool", params={"val": 42}, risk_level=1, requires_consensus=False)
    result = await agent.act(plan)

    assert result.status == "success"
    assert result.data["val"] == 42

@pytest.mark.asyncio
async def test_multi_agent_orchestration(tc):
    agent1 = ArkheAgent(agent_id="agent1", agent_type="Diag", version="1.0", tc=tc)
    agent2 = ArkheAgent(agent_id="agent2", agent_type="Diag", version="1.0", tc=tc)

    async def diag_handler(params):
        return {"status": "success"}

    tool = ToolSpec(name="diagnose", description="", parameters_schema={}, permission=ToolPermission.READ_ONLY, handler=diag_handler, risk_level=1)
    agent1.toolset.register(tool)
    agent2.toolset.register(tool)

    orchestrator = MultiAgentOrchestrator(tc, [agent1, agent2])
    task = TaskSpec(task_id="t1", type="diagnostic", target="system", required_skills=[])

    result = await orchestrator.execute_task(task)
    assert result["status"] == "completed"
    assert len(result["results"]) == 2
    assert result["results"][0] == "success"
    assert result["results"][1] == "success"
