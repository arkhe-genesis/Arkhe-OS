"""
Arkhe OS — Substrato 9029: Superlinked SIE Integration Launcher
"""

import sys
import logging
import importlib.util

# Use importlib.util to dynamically load the module from a path containing numbers
module_name = 'sie_integration'
module_path = 'substrates/9029_superlinked_sie/sie_integration.py'
spec = importlib.util.spec_from_file_location(module_name, module_path)
sie_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = sie_module
spec.loader.exec_module(sie_module)

SIEIntegration = sie_module.SIEIntegration
mcp = sie_module.mcp

def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  ARKHE OS — Substrato 9029                       ║")
    print("║  Superlinked SIE (Inference Engine) Integration  ║")
    print("╚══════════════════════════════════════════════════╝")
    print("")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Mock TemporalChain and GuardianAttractor
    class MockTemporalChain:
        def anchor_event(self, event_type, payload):
            logging.info(f"MOCK TC ANCHOR [{event_type}]: {payload}")
            return "mock_anchor"

    class MockGuardian:
        def model_attack_paths(self):
            return []

    tc = MockTemporalChain()
    guardian = MockGuardian()

    sie = SIEIntegration(temporal_chain=tc, guardian_attractor=guardian)
    print("\n✅ SIE Integration Initialized")
    print(f"   Registered Models: {list(sie.sie.models.keys())}")
    print(f"   Live Backend Reached: {sie.sie.is_live}")

    print("\n🔹 Testing Encode Primitive...")
    texts = ["Arkhe OS is a robust system.", "Superlinked SIE optimizes small models."]
    embeddings = sie.encode_text(texts)
    print(f"   Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}.")

    print("\n🔹 Testing Score Primitive...")
    query = "What is Arkhe?"
    scores = sie.score_documents(query, texts)
    print(f"   Scores: {scores}")

    print("\n🔹 Testing Extract Primitive...")
    schema = {"type": "person"}
    entities = sie.extract_entities(texts, schema)
    print(f"   Extracted Entities: {entities}")

    print("\n🚀 Starting FastMCP Server for stdio transport...")
    if "--mcp" in sys.argv:
        # Run MCP stdio server
        mcp.run()
    else:
        print("   (Run with '--mcp' to start the actual stdio MCP server loop)")

if __name__ == "__main__":
    sys.exit(main())
