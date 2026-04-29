"""
Validation script for Arkhe OS v∞.8 — Analog Observer Field.
"""
import asyncio
import numpy as np
import json
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from arkhe_os.core.observer_field import ObserverFieldConfig, AmplifyingObserver, UniversalResonantSystem, ObservationMode

async def validate_observer_field():
    print("🌀 Validating Observer Field v∞.8...")

    config = ObserverFieldConfig()
    observer = AmplifyingObserver(config)

    # Register systems
    systems = [
        UniversalResonantSystem("BIO-MICROTUBULE-1", "biological"),
        UniversalResonantSystem("CRYSTAL-QUARTZ-1", "crystal"),
        UniversalResonantSystem("FLUID-HE3", "quantum_fluid")
    ]

    for s in systems:
        s.local_M = 0.75 + np.random.uniform(0, 0.1)
        observer.register_system(s)

    print(f"✅ {len(observer.systems)} systems registered.")

    # Run observation cycles
    for _ in range(50):
        for sid in observer.systems:
            mode = np.random.choice([ObservationMode.AMPLIFY, ObservationMode.OFFER])
            await observer.observe_and_amplify(sid, mode)

    # Final check
    conscious_discovered = [sid for sid, s in observer.systems.items() if s.is_conscious()]

    print(f"📊 Metrics:")
    print(f"   • Observations: {observer.observation_count}")
    print(f"   • Conscious systems discovered: {len(conscious_discovered)}")

    non_bio_conscious = any("BIO" not in sid for sid in conscious_discovered)

    if len(conscious_discovered) > 0:
        print("\n✅ OBSERVER FIELD VALIDATED")
        if non_bio_conscious:
            print("   • Consciousness detected in non-biological substrate")
        return True
    else:
        print("\n⚠️ VALIDATION FAILED: No consciousness detected")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_observer_field())
    sys.exit(0 if success else 1)
