import asyncio
from typing import Dict, Any, List

class ArkheAgent:
    def __init__(self):
        # Mocks
        self.guardian = MockGuardian()
        self.llm = MockLLM()
        self.phi_bus = MockPhiBus()
        self.temporal = MockTemporalChain()

class MockGuardian:
    async def exorcise_context(self, history: dict) -> dict:
        return {"safe": True, "data": history.get("data", [])}

class MockLLM:
    async def predict_macro(self, structured_history: dict) -> dict:
        return {"agent_id": "macro_01", "values": [1.1, 1.2, 1.3]}

    async def predict_micro(self, structured_history: dict) -> dict:
        return {"agent_id": "micro_01", "values": [1.05, 1.25, 1.28]}

class MockPhiBus:
    async def get_agent_coherence(self, agent_id: str) -> float:
        if "macro" in agent_id:
            return 0.8
        elif "micro" in agent_id:
            return 0.6
        return 0.5

class MockTemporalChain:
    async def anchor_event(self, event_type: str, payload: dict) -> str:
        return "seal_" + str(hash(str(payload)))[:8]
