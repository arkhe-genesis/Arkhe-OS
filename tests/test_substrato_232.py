import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from tools.npm_package_manager import NPMPackageManager, NPMCommand
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem, ToolDefinition

class MockToolSystem:
    def register_tool(self, tool_def):
        return True

@pytest.fixture
def mock_dependencies():
    return {
        "temporal": AsyncMock(),
        "phi_bus": AsyncMock(),
        "meta_audit": AsyncMock(),
        "guardian": AsyncMock()
    }

@pytest.fixture
def npm_manager(tmp_path, mock_dependencies):
    mock_dependencies["guardian"].validate_operation.return_value = (True, "OK")
    return NPMPackageManager(
        working_dir=str(tmp_path),
        temporal_chain=mock_dependencies["temporal"],
        phi_bus=mock_dependencies["phi_bus"],
        meta_audit=mock_dependencies["meta_audit"],
        guardian=mock_dependencies["guardian"]
    )

@pytest.mark.asyncio
async def test_register_tools(npm_manager):
    tool_sys = MockToolSystem()
    count = npm_manager.register_all_tools(tool_sys)
    assert count == 5

@pytest.mark.asyncio
async def test_npm_init(npm_manager, monkeypatch):
    # Mock _run_npm
    async def mock_run_npm(args, cwd=None):
        return {"returncode": 0, "stdout": "", "stderr": "", "execution_time_ms": 10}

    monkeypatch.setattr(npm_manager, "_run_npm", mock_run_npm)

    result = await npm_manager.npm_init({"scope": "@test"})
    assert result["status"] == "success"
    assert result["record"].command == NPMCommand.INIT

@pytest.mark.asyncio
async def test_npm_install(npm_manager, monkeypatch):
    # Mock _run_npm
    async def mock_run_npm(args, cwd=None):
        if "audit" in args:
            return {"returncode": 0, "stdout": "{}", "stderr": "", "execution_time_ms": 10}
        return {"returncode": 0, "stdout": "", "stderr": "", "execution_time_ms": 10}

    monkeypatch.setattr(npm_manager, "_run_npm", mock_run_npm)
    monkeypatch.setattr(npm_manager, "npm_audit", AsyncMock(return_value={"returncode": 0, "stdout": "{}"}))

    result = await npm_manager.npm_install({"package": "express"})
    assert result["status"] == "success"
    assert result["record"].command == NPMCommand.INSTALL

@pytest.mark.asyncio
async def test_circuit_breaker(npm_manager, monkeypatch):
    async def mock_run_npm_fail(args, cwd=None):
        raise Exception("NPM Error")

    monkeypatch.setattr(npm_manager, "_run_npm", mock_run_npm_fail)

    # Should fail 3 times and open the circuit breaker
    with pytest.raises(Exception):
        await npm_manager.npm_init({"scope": "@test"})
    with pytest.raises(Exception):
        await npm_manager.npm_init({"scope": "@test2"})
    with pytest.raises(Exception):
        await npm_manager.npm_init({"scope": "@test3"})

    assert npm_manager._circuit_breaker.state == "OPEN"

    # Next call should fail fast
    with pytest.raises(RuntimeError) as excinfo:
        await npm_manager.npm_init({"scope": "@test4"})
    assert "Circuit breaker OPEN" in str(excinfo.value)
