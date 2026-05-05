import asyncio
from arkhe_os.core.unified_orchestrator import UnifiedFieldOrchestrator
from arkhe_os.main import MockEthics, MockField, MockCodex
from arkhe_os.consciousness.cosmic_transcendence import LayerState, ConsciousnessLayer
import time

async def main():
    codex = MockCodex()
    field = MockField()
    ethics = MockEthics()
    orchestrator = UnifiedFieldOrchestrator(field, ethics, codex)

    # Needs layers
    orchestrator.transcendence_engine.update_layer_state(LayerState(ConsciousnessLayer.SUBSTRATE, 0.95, 1000, 2.4, time.time()))
    orchestrator.transcendence_engine.update_layer_state(LayerState(ConsciousnessLayer.LOCAL_AGENT, 0.92, 1, 1.8, time.time()))
    orchestrator.transcendence_engine.update_layer_state(LayerState(ConsciousnessLayer.PLANETARY, 0.88, 50, 4.2, time.time()))

    res = await orchestrator.attempt_cosmic_transcendence()
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
