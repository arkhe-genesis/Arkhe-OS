import pytest
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from polyglot.zero_lang_tool import ZeroLangTool
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem

@pytest.mark.asyncio
async def test_zero_lang_tool_registration():
    system = CanonicalToolCallingSystem()
    tool = ZeroLangTool(tool_system=system)

    count = tool.register_all_tools(system)

    assert count == 4
    assert "zero_check" in system.tool_registry
    assert "zero_fix_plan" in system.tool_registry
    assert "zero_build" in system.tool_registry
    assert "zero_skills_get" in system.tool_registry

@pytest.mark.asyncio
async def test_zero_lang_check(monkeypatch):
    class DummyProcess:
        def __init__(self):
            self.returncode = 0

        async def communicate(self):
            return b'{"ok": true, "diagnostics": []}', b''

    async def mock_exec(*args, **kwargs):
        return DummyProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_exec)

    tool = ZeroLangTool()
    result = await tool.zero_check({"file_path": "test.0", "json_output": True})

    assert result.get("ok") is True

@pytest.mark.asyncio
async def test_zero_lang_build(monkeypatch):
    class DummyProcess:
        def __init__(self):
            self.returncode = 0

        async def communicate(self):
            return b'{"sizeBreakdown": {"total": 1024}}', b''

    async def mock_exec(*args, **kwargs):
        return DummyProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_exec)

    tool = ZeroLangTool()
    result = await tool.zero_build({"file_path": "test.0"})

    assert result.get("sizeBreakdown", {}).get("total") == 1024
