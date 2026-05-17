import asyncio
import pytest
from engineering.server_driven_core import ServerDrivenUIRenderer, PerformanceOptimizer, MigrationOrchestrator, DIContainer, UIComponentType, UIViewNode
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem, ToolCallRequest

class MockObservability:
    async def log_tool_execution(self, *args, **kwargs): pass
class MockPQC:
    def sign_result(self, *args, **kwargs): return "mock_sig"
class MockTemporal:
    async def anchor_event(self, *args, **kwargs): return "mock_hash"

@pytest.mark.asyncio
async def test_sdui_rendering():
    pqc = MockPQC()
    tool_system = CanonicalToolCallingSystem(MockObservability(), pqc)
    tool_system.temporal = MockTemporal()

    sdui = ServerDrivenUIRenderer(tool_system)
    node = UIViewNode(
        component=UIComponentType.CARD,
        props={"title": "Test Card"},
        children=[
            UIViewNode(component=UIComponentType.TEXT, props={"text": "Hello"}, children=[])
        ]
    )
    res = await sdui.render(node, platform="web")
    assert res["platform"] == "web"
    assert res["view"]["type"] == "card"
    assert res["view"]["title"] == "Test Card"
    assert res["view"]["children"][0]["type"] == "text"
    assert res["view"]["children"][0]["content"] == "Hello"

@pytest.mark.asyncio
async def test_performance_optimizer():
    perf = PerformanceOptimizer()

    calls = 0
    @perf.cached(ttl_seconds=10)
    async def my_func(x):
        nonlocal calls
        calls += 1
        return x * 2

    assert await my_func(5) == 10
    assert calls == 1
    assert await my_func(5) == 10
    assert calls == 1

@pytest.mark.asyncio
async def test_di_container():
    di = DIContainer()
    di.register("MyService", lambda: {"val": 42}, lifecycle="singleton")

    @di.inject
    async def handler(MyService: "MyService" = None):
        return MyService["val"]

    assert await handler() == 42

@pytest.mark.asyncio
async def test_migration_orchestrator():
    tool_system = CanonicalToolCallingSystem(MockObservability(), MockPQC())
    tool_system.temporal = MockTemporal()
    migrator = MigrationOrchestrator(tool_system)

    res = await migrator.canary_deploy("payment_svc", "v2.0", 15)
    assert res["status"] == "canary"
    assert res["percent"] == 15
