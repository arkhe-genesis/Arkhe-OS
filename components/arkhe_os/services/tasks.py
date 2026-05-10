import asyncio
import logging

async def optimize_infrastructure_task(scaffold_state):
    """
    Background task to simulate auto-operation.
    Adjusts system parameters based on coherence.
    """
    while True:
        m = scaffold_state.coherence_M
        if m < 0.85:
            logging.info(f"Low Coherence detected (M={m:.4f}). Triggering auto-optimization...")
            # Simulate optimization logic
            scaffold_state.turbulence *= 0.95
        await asyncio.sleep(60) # Run every minute
