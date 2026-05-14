import pytest
import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'substrates/9012_arkhe_ipython/src')))

from arkhe_ipython.utils import SafeCoreConnection, format_phi_c_display
from arkhe_ipython.magics import ArkheMagics
from arkhe_ipython.kernel import ArkheKernel
from traitlets.config.configurable import Configurable

class MockShell(Configurable):
    pass

@pytest.fixture
def mock_safe_core():
    conn = SafeCoreConnection()
    conn.call_tool = MagicMock()
    conn.query_audit = MagicMock()
    return conn

@pytest.mark.asyncio
async def test_magics_status(mock_safe_core):
    mock_shell = MockShell()
    magics = ArkheMagics(mock_shell)
    magics.safe_core = mock_safe_core

    # Configure an async side effect / return value
    async def mock_call_tool(tool_name, args):
        if tool_name == "phi_c_status":
            return {
                "current_phi_c": 0.998,
                "active_profile": "technical"
            }
        return {}

    mock_safe_core.call_tool = mock_call_tool

    result = await magics._execute_command("status", [])
    assert result["node_status"] == "online"
    assert result["phi_c_coherence"] == 0.998
    assert result["active_profile"] == "technical"

def test_phi_c_display():
    assert format_phi_c_display(0.995) == "🟢 0.9950"
    assert format_phi_c_display(0.955) == "🟡 0.9550"
    assert format_phi_c_display(0.905) == "🟠 0.9050"
    assert format_phi_c_display(0.850) == "🔴 0.8500"
