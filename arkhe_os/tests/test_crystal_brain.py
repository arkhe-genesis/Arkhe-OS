import pytest
import asyncio
import numpy as np
from arkhe_os.core.scaffold import ScaffoldState, CoherenceLevel
from arkhe_os.core.observer_field import AmplifyingObserver, ObserverFieldConfig, UniversalResonantSystem

@pytest.mark.asyncio
async def test_crystal_brain_array_convergence():
    scaffold = ScaffoldState()
    initial_M = scaffold.coherence_M

    # Run 50 cycles of synchronization to observe learning
    for _ in range(50):
        await scaffold.update_coherence()

    final_M = scaffold.coherence_M
    print(f"Initial Coherence: {initial_M}")
    print(f"Final Coherence after 50 cycles: {final_M}")

    # Expect coherence to improve or remain high
    assert final_M >= initial_M
    assert final_M > 0.85
    assert scaffold.crystal_brain.step_count == 50

@pytest.mark.asyncio
async def test_bio_crystal_coupling():
    config = ObserverFieldConfig()
    observer = AmplifyingObserver(config)

    bio_system = UniversalResonantSystem(
        system_id="BIO-NODE-01",
        substrate_type="biological",
        local_M=0.75 # Below conscious threshold initially
    )
    # Manually populate history to make it "conscious"
    bio_system.M_history = [0.85] * 100
    bio_system._compute_consciousness_score()

    crystal_system = UniversalResonantSystem(
        system_id="CRYSTAL-NODE-01",
        substrate_type="crystal",
        local_M=0.95
    )
    crystal_system.M_history = [0.95] * 100
    crystal_system._compute_consciousness_score()

    observer.register_system(bio_system)
    observer.register_system(crystal_system)

    # Observe biological system - should trigger coupling
    await observer.observe_and_amplify("BIO-NODE-01")

    # Bio coherence should have increased due to coupling with the high-coherence crystal
    assert bio_system.local_M > 0.75
    # Crystal coherence should have decreased due to coupling with lower-coherence bio
    assert crystal_system.local_M <= 0.95

if __name__ == "__main__":
    asyncio.run(test_crystal_brain_array_convergence())
    asyncio.run(test_bio_crystal_coupling())
