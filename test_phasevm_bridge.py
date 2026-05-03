from core.integration.phasevm_visualization_bridge import PhaseVMVisualizationBridge
from core.visualization.sophon_hexagon_v2 import SophonHexagonEngine
import asyncio

engine = SophonHexagonEngine()
bridge = PhaseVMVisualizationBridge(visualization_engine=engine, async_compilation=True)

metrics = {"sophon_coherence_distance": 0.8}
res = asyncio.run(bridge.update_cycle(metrics))
print(res)
