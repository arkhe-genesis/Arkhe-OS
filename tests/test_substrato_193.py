import pytest
import asyncio
from forecasting.nexus_agents import ContextAgent, MacroAgent, MicroAgent, SynthesizerAgent
from forecasting.quantum_calibration import QuantumCalibrator, MockQBusClient

@pytest.mark.asyncio
async def test_context_agent():
    agent = ContextAgent()
    result = await agent.process({"data": [{"time": "t", "value": 1}]})
    assert "timeline" in result
    assert len(result["timeline"]) == 1

@pytest.mark.asyncio
async def test_dual_reasoning():
    macro = MacroAgent()
    micro = MicroAgent()

    macro_res = await macro.reason({"timeline": []})
    micro_res = await micro.reason({"timeline": []})

    assert "values" in macro_res
    assert "values" in micro_res

@pytest.mark.asyncio
async def test_synthesizer_agent():
    agent = SynthesizerAgent()
    macro = {"agent_id": "macro_1", "values": [1.0, 2.0]}
    micro = {"agent_id": "micro_1", "values": [0.5, 1.5]}

    res = await agent.synthesize(macro, micro, [])
    assert "values" in res
    assert len(res["values"]) == 2
    assert "temporal_seal" in res

@pytest.mark.asyncio
async def test_quantum_calibration():
    calibrator = QuantumCalibrator(MockQBusClient())
    guidelines = await calibrator.optimize_guidelines([1, 2, 3])
    assert isinstance(guidelines, list)
    assert len(guidelines) > 0
