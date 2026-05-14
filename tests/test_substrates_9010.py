import pytest
import asyncio
import os
import sys
import importlib.util

# Add src to pythonpath so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from arkhe.layers.constraints import TemporalChainClient as TemporalChain

# Dynamically load the module because of the starting number in directory name
module_name = 'secure_dev_core'
module_path = os.path.join(os.path.dirname(__file__), '..', 'substrates', '9010_multi_llm_core', 'secure_dev_core.py')
spec = importlib.util.spec_from_file_location(module_name, module_path)
secure_dev_core = importlib.util.module_from_spec(spec)
sys.modules[module_name] = secure_dev_core
spec.loader.exec_module(secure_dev_core)

MultiLLMSecureDevCore = secure_dev_core.MultiLLMSecureDevCore
SecureDevTask = secure_dev_core.SecureDevTask
LLMAgentConfig = secure_dev_core.LLMAgentConfig
MA_S2_Role = secure_dev_core.MA_S2_Role


class AsyncTemporalChainClient(TemporalChain):
    async def anchor_event(self, event_type, data):
        content_hash = hash(str(data))
        return self.anchor_content(content_hash, {"type": event_type})

class MockGuardian:
    class MockExorcist:
        def exorcise_token(self, *args, **kwargs):
            return (True, type('obj', (object,), {'severity_score': 0.37}))

    def __init__(self):
        self.exorcist = self.MockExorcist()
        self.vocab_embeddings = [[0.0]]

@pytest.fixture
def test_setup():
    temporal = AsyncTemporalChainClient()
    guardian = MockGuardian()

    agents = {
        MA_S2_Role.CVS_AGENT: LLMAgentConfig(role=MA_S2_Role.CVS_AGENT, model="Claude-3.5-Sonnet", endpoint="...", credentials="..."),
        MA_S2_Role.APM_AGENT: LLMAgentConfig(role=MA_S2_Role.APM_AGENT, model="GPT-4", endpoint="...", credentials="..."),
        MA_S2_Role.INV_AGENT: LLMAgentConfig(role=MA_S2_Role.INV_AGENT, model="Kimi-Cathedral", endpoint="...", credentials="..."),
        MA_S2_Role.AUDITOR: LLMAgentConfig(role=MA_S2_Role.AUDITOR, model="LLaMA-3-70B", endpoint="...", credentials="..."),
    }

    core = MultiLLMSecureDevCore(agents=agents, phi_c_bus=None, temporal_chain=temporal, guardian=guardian)
    return core

@pytest.mark.asyncio
async def test_evaluate_code_security(test_setup):
    core = test_setup

    insecure_code = """
import pickle
import os

def load_user_data(filename):
    data = open(filename, 'rb').read()
    return pickle.loads(data)  # Unsafe deserialization

def execute_command(cmd):
    os.system(cmd)  # Command injection
"""

    task = SecureDevTask(
        task_id="SEC-2026-001",
        code_snippet=insecure_code,
        context={"language": "python", "framework": "none"},
        security_level="high",
        trace_id="TRACE_ID_MOCKED"
    )

    result = await core.evaluate_code_security(task)

    assert result["task_id"] == "SEC-2026-001"
    assert "cvs" in result["results"]
    assert "apm" in result["results"]
    assert "inv" in result["results"]
    assert "audit" in result["results"]
    assert "guardian" in result["results"]

    assert abs(result["results"]["guardian"]["severity"] - 0.37) < 0.001

    assert result["consensus"]["status"] == "review"
    assert abs(result["consensus"]["avg_severity"] - 0.72) < 0.001
    assert abs(result["consensus"]["phi_c_coherence"] - 0.928) < 0.001
