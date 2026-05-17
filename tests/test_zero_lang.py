import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from polyglot.zero_lang_tool import ZeroLangTool
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem, ToolDefinition

class MockProcess:
    def __init__(self, stdout, stderr, returncode):
        self.stdout = stdout.encode()
        self.stderr = stderr.encode()
        self.returncode = returncode

    async def communicate(self):
        return self.stdout, self.stderr

@pytest.fixture
def mock_subprocess(monkeypatch):
    async def mock_exec(*args, **kwargs):
        cmd = " ".join(args)
        if "check" in cmd:
            return MockProcess('{"ok": true, "diagnostics": []}', "", 0)
        elif "fix" in cmd:
            return MockProcess('{"plan": "mock_plan"}', "", 0)
        elif "build" in cmd:
            return MockProcess('{"sizeBreakdown": {"total": 1024}}', "", 0)
        elif "skills" in cmd:
            return MockProcess('mock_skills_data', "", 0)
        elif "new" in cmd:
            return MockProcess('created', "", 0)
        return MockProcess("", "", 1)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_exec)

@pytest.mark.asyncio
async def test_zero_check(mock_subprocess):
    tool = ZeroLangTool()
    res = await tool.zero_check("test.0")
    assert res.get("ok") is True

@pytest.mark.asyncio
async def test_zero_fix_plan(mock_subprocess):
    tool = ZeroLangTool()
    res = await tool.zero_fix_plan("test.0")
    assert res.get("plan") == "mock_plan"

@pytest.mark.asyncio
async def test_zero_build(mock_subprocess):
    tool = ZeroLangTool()
    res = await tool.zero_build("test.0")
    assert res.get("sizeBreakdown", {}).get("total") == 1024

@pytest.mark.asyncio
async def test_zero_skills_get(mock_subprocess):
    tool = ZeroLangTool()
    res = await tool.zero_skills_get()
    assert res["stdout"] == "mock_skills_data"

def test_register_all_tools():
    tool_system = CanonicalToolCallingSystem()
    tool = ZeroLangTool(tool_system=tool_system)
    count = tool.register_all_tools(tool_system)

    assert count == 5
    assert "zero_check" in tool_system.tool_registry
    assert "zero_fix_plan" in tool_system.tool_registry
    assert "zero_build" in tool_system.tool_registry
    assert "zero_skills_get" in tool_system.tool_registry
    assert "zero_new_project" in tool_system.tool_registry
