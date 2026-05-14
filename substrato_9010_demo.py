#!/usr/bin/env python3
"""Demonstração do núcleo multi‑LLM avaliando um trecho de código inseguro."""

import asyncio
import json
import os
import sys

# Add src to pythonpath so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from substrates.9010_multi_llm_core.secure_dev_core import MultiLLMSecureDevCore, SecureDevTask, LLMAgentConfig, MA_S2_Role
from arkhe.security import GuardianAttractor, ThreatDatabase
from arkhe.chain import TemporalChain

async def demo():
    temporal = TemporalChain()
    guardian = GuardianAttractor(ThreatDatabase())

    # Configurar agentes LLM
    agents = {
        MA_S2_Role.CVS_AGENT: LLMAgentConfig(role=MA_S2_Role.CVS_AGENT, model="Claude-3.5-Sonnet", endpoint="...", credentials="..."),
        MA_S2_Role.APM_AGENT: LLMAgentConfig(role=MA_S2_Role.APM_AGENT, model="GPT-4", endpoint="...", credentials="..."),
        MA_S2_Role.INV_AGENT: LLMAgentConfig(role=MA_S2_Role.INV_AGENT, model="Kimi-Cathedral", endpoint="...", credentials="..."),
        MA_S2_Role.AUDITOR: LLMAgentConfig(role=MA_S2_Role.AUDITOR, model="LLaMA-3-70B", endpoint="...", credentials="..."),
    }

    core = MultiLLMSecureDevCore(agents=agents, phi_c_bus=None, temporal_chain=temporal, guardian=guardian)

    # Código vulnerável de exemplo
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
        security_level="high"
    )

    result = await core.evaluate_code_security(task)
    # Don't print the temporal_seal as it changes every run
    if "temporal_seal" in result:
        del result["temporal_seal"]
    if "timestamp" in result:
        del result["timestamp"]
    if "trace_id" in result:
        result["trace_id"] = "TRACE_ID_MOCKED"

    # Mocking the sbom_hash as well as it depends on code snippet and hash algorithm which is fixed but just to be sure
    if "inv" in result["results"] and "sbom_hash" in result["results"]["inv"]:
         result["results"]["inv"]["sbom_hash"] = "SBOM_HASH_MOCKED"

    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(demo())
