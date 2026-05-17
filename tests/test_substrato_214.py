import pytest
import asyncio
import os
import shutil
from substrato_214_installer_cathedral import InnoSetupTool

class MockTemporalChain:
    def __init__(self):
        self.events = []

    async def anchor_event(self, event_type: str, metadata: dict):
        self.events.append({"type": event_type, "metadata": metadata})
        return "mock_seal"

class MockDeltaMem:
    def __init__(self):
        self.experiences = []

    async def write_experience(self, exp_type: str, features: dict):
        self.experiences.append({"type": exp_type, "features": features})

@pytest.mark.asyncio
async def test_generate_iss_template():
    tool = InnoSetupTool()
    res = await tool.generate_iss_template({
        "app_name": "Test App",
        "version": "2.0.0",
        "publisher": "Test Pub"
    })

    assert res["app_name"] == "Test App"
    assert res["version"] == "2.0.0"
    assert "AppName=Test App" in res["script_content"]
    assert "AppVersion=2.0.0" in res["script_content"]
    assert "AppPublisher=Test Pub" in res["script_content"]

@pytest.mark.asyncio
async def test_compile_installer_idempotency_and_hsm():
    temporal = MockTemporalChain()
    delta_mem = MockDeltaMem()
    tool = InnoSetupTool(temporal=temporal, delta_mem=delta_mem)

    test_out_dir = "./test_build_dir"
    if os.path.exists(test_out_dir):
        shutil.rmtree(test_out_dir)

    params = {
        "script_content": "mock script data",
        "installer_name": "test_setup.exe",
        "output_dir": test_out_dir,
        "sign_with_hsm": True
    }

    # First run (no cache)
    res1 = await tool.compile_installer(params)
    assert res1["cache_hit"] is False
    assert res1["installer_name"] == "test_setup.exe"
    assert "dilithium3" in res1["signature"]
    assert os.path.exists(os.path.join(test_out_dir, "test_setup.exe"))

    # Temporal event should be logged
    assert len(temporal.events) == 1
    assert temporal.events[0]["type"] == "installer_compiled"
    assert temporal.events[0]["metadata"]["signed"] is True

    # delta_mem experience should be logged
    assert len(delta_mem.experiences) == 1
    assert delta_mem.experiences[0]["type"] == "inno_build"
    assert delta_mem.experiences[0]["features"]["success"] is True

    # Second run (cache hit)
    res2 = await tool.compile_installer(params)
    assert res2["cache_hit"] is True
    assert res2["installer_name"] == "test_setup.exe"
    assert res2["script_hash"] == res1["script_hash"]

    # Temporal should not be called again for cache hit
    assert len(temporal.events) == 1

    # delta_mem should not be called again for cache hit
    assert len(delta_mem.experiences) == 1

    # Cleanup
    shutil.rmtree(test_out_dir)
