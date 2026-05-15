import asyncio
import logging
from forecasting.nexus_agents import ContextAgent, MacroAgent, MicroAgent, SynthesizerAgent
from forecasting.quantum_calibration import QuantumCalibrator, MockQBusClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Substrato_193")

async def run_forecasting_mesh():
    logger.info("Initializing Arkhe Forecasting Mesh (Substrato 193)...")

    context_agent = ContextAgent()
    macro_agent = MacroAgent()
    micro_agent = MicroAgent()
    synth_agent = SynthesizerAgent()
    calibrator = QuantumCalibrator(MockQBusClient())

    raw_history = {
        "data": [
            {"time": "t-3", "value": 1.0},
            {"time": "t-2", "value": 1.05},
            {"time": "t-1", "value": 1.02}
        ]
    }

    logger.info("1. Contextualization...")
    structured_timeline = await context_agent.process(raw_history)
    logger.info(f"Structured timeline: {structured_timeline}")

    logger.info("2. Quantum Calibration (Backtest Split Evaluation)...")
    backtest_splits = [raw_history, raw_history] # Mock splits
    guidelines = await calibrator.optimize_guidelines(backtest_splits)
    logger.info(f"Optimized guidelines from Q-Bus: {guidelines}")

    logger.info("3. Dual Reasoning (Macro & Micro)...")
    macro_forecast = await macro_agent.reason(structured_timeline)
    micro_forecast = await micro_agent.reason(structured_timeline)
    logger.info(f"Macro forecast: {macro_forecast}")
    logger.info(f"Micro forecast: {micro_forecast}")

    logger.info("4. Synthesis & Calibration...")
    final_result = await synth_agent.synthesize(macro_forecast, micro_forecast, guidelines)
    logger.info(f"Final Synthesized Forecast: {final_result}")

    logger.info("================================================================")
    logger.info("ARKHE FORECASTING MESH ACTIVATED - TEMPORAL SEAL ACQUIRED")
    logger.info(f"SEAL: {final_result['temporal_seal']}")
    logger.info("================================================================")

if __name__ == "__main__":
    asyncio.run(run_forecasting_mesh())
