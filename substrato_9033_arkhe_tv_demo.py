#!/usr/bin/env python3
"""
Substrato 9033 — Arkhe TV: Integração Arkhe TV Demo
Integração Arkhe TV Demo
"""
import asyncio
from arkhe_tv.deepfake_detector import DeepfakeDetector
from arkhe_tv.ldm_controller import LDMController, LDMConfig, LDMMode

async def demo():
    print("=" * 60)
    print("ARKHE TV — Deepfake Detector & LDM Controller Demo")
    print("=" * 60)

    # 1. Deepfake Detector
    print("\n🔍 Deepfake Detection:")
    detector = DeepfakeDetector()

    # Simular 60 frames (2 segundos a 30fps)
    frames = [f"frame_{i:04d}_data".encode() for i in range(60)]
    report = await detector.analyze_stream("live_channel_7", frames)

    print(f"   Content ID: {report.content_id}")
    print(f"   Verdict: {report.verdict.value}")
    print(f"   Max Score: {report.max_score:.4f}")
    print(f"   Avg Score: {report.avg_score:.4f}")
    print(f"   Suspicious: {report.suspicious_frames}/{report.total_frames}")
    print(f"   Φ_C Impact: {report.phi_c_impact:+.3f}")
    if report.temporal_seal:
        print(f"   Seal: {report.temporal_seal}")

    # 2. LDM Controller
    print("\n📡 LDM Controller:")

    # Mock do adapter XOS
    class MockXOS:
        async def get_active_plps(self):
            return [
                type('PLP', (), {'plp_id': 1, 'cnr_threshold_db': 28, 'bitrate_mbps': 8.0, 'phi_c': 0.97}),
                type('PLP', (), {'plp_id': 2, 'cnr_threshold_db': 22, 'bitrate_mbps': 18.0, 'phi_c': 0.94}),
            ]
        async def set_ldm_config(self, core_plp, enhanced_plp, injection_db):
            print(f"   → XOS API: set LDM injection={injection_db}dB")

    ldm = LDMController(
        xos_adapter=MockXOS(),
        config=LDMConfig(core_plp_id=1, enhanced_plp_id=2, injection_level_db=-10.0, mode=LDMMode.ADAPTIVE),
    )

    # Executar algumas iterações
    for i in range(5):
        new_inj = await ldm.optimize()
        metrics = ldm.history[-1]
        print(f"   Iter {i+1}: injection={new_inj:.1f}dB | Φ_C={metrics.phi_c_coherence:.4f} | "
              f"CL={metrics.core_bitrate_mbps:.1f}Mbps | EL={metrics.enhanced_bitrate_mbps:.1f}Mbps")

    print("\n✅ Demo completed")

if __name__ == "__main__":
    asyncio.run(demo())