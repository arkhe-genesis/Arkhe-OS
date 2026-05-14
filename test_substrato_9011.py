#!/usr/bin/env python3
import asyncio
import importlib.util
import unittest

spec = importlib.util.spec_from_file_location(
    "human_synthesis_engine",
    "substrates/9011_human_synthesis/human_synthesis_engine.py"
)
human_synthesis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(human_synthesis)

HumanSynthesisEngine = human_synthesis.HumanSynthesisEngine
SynthesisParadigm = human_synthesis.SynthesisParadigm
SecureDevTask = human_synthesis.SecureDevTask

class MockFinding:
    def enrich_with_epss_kev(self):
        pass
    def to_dict(self):
        return {"id": "mock-finding-cvs-0.1"}

class MockAttackPath:
    def to_dict(self):
        return {"id": "mock-path-apm-1.1"}

class MockGuardian:
    async def scan_artifact(self, artifact_hash: str):
        return [MockFinding()]
    def model_attack_paths(self, service_map: dict):
        return [MockAttackPath()]

class MockMultiLLM:
    async def evaluate_code_security(self, task: SecureDevTask):
        return {"consensus": {"status": "approved", "phi_c": 0.99}}

class MockTemporalChain:
    async def anchor_event(self, event_type: str, data: dict):
        return f"seal-{data.get('hash', 'unknown')}"

class TestSubstrato9011(unittest.IsolatedAsyncioTestCase):
    async def test_generation_approved(self):
        guardian = MockGuardian()
        multi_llm = MockMultiLLM()
        temporal = MockTemporalChain()
        engine = HumanSynthesisEngine(guardian, multi_llm, temporal)

        prompt = {
            "subject": "A futuristic human digital avatar",
            "pose": "standing",
            "style": "photorealistic"
        }
        result = await engine.generate(SynthesisParadigm.HYBRID, prompt, security_level="high")

        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["image_hash"].isalnum())
        self.assertEqual(result["temporal_seal"], f"seal-{result['image_hash']}")
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["id"], "mock-finding-cvs-0.1")
        self.assertEqual(len(result["attack_paths"]), 1)
        self.assertEqual(result["attack_paths"][0]["id"], "mock-path-apm-1.1")

if __name__ == '__main__':
    unittest.main()
