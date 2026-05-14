import asyncio
from src.arkhe.core.cross_platform.mobile_adapters import iOSAdapter, AndroidAdapter
from src.arkhe.core.cross_platform.wasm_runtime import WebAssemblyAdapter
from src.arkhe.core.cross_platform.mobile_sync_optimizer import MobileSyncOptimizer, NetworkCondition, SyncCompressionConfig

async def test_all():
    print("Testing iOS Adapter...")
    ios = iOSAdapter()
    print("Capabilities:", ios.get_platform_capabilities().platform)
    seal = ios.compute_platform_seal(b"test")
    print("Seal:", seal)

    print("\nTesting Android Adapter...")
    android = AndroidAdapter()
    print("Capabilities:", android.get_platform_capabilities().platform)
    seal = android.compute_platform_seal(b"test")
    print("Seal:", seal)

    print("\nTesting WebAssembly Adapter...")
    wasm = WebAssemblyAdapter()
    print("Capabilities:", wasm.get_platform_capabilities().platform)
    seal = wasm.compute_platform_seal(b"test")
    print("Seal:", seal)

    print("\nTesting Sync Optimizer...")
    optimizer = MobileSyncOptimizer()
    payload = {"data": "test" * 100, "phi_c_coherence": 0.99, "temporal_anchor": "1234567890"}
    config = SyncCompressionConfig(network_condition=NetworkCondition.CELLULAR_3G)
    compressed, metadata = await optimizer.prepare_payload_for_sync(payload, config)
    print("Original size:", metadata.original_size)
    print("Compressed size:", metadata.compressed_size)
    print("Ratio:", metadata.compression_ratio)

if __name__ == "__main__":
    asyncio.run(test_all())

    print("\nTesting Next-Gen Mobile/Web Features (Substrato 7.9.1)...")
    from substrato_791_mobile_web_next import WasmOptimizer, PushNotificationService, PWAManager, MobilePowerOptimizer, AdaptiveUIAdapter

    wasm_opt = WasmOptimizer()
    print("WASM Optimization:", wasm_opt.optimize_bundle_for_progressive_loading("arkhe_core.wasm"))

    push_service = PushNotificationService()
    print("Push Notification:", push_service.send_phi_c_alert("user_123", 0.98, "Φ_C Sync Restored"))

    pwa_manager = PWAManager()
    print("PWA Manifest:", pwa_manager.generate_pwa_manifest("Arkhe Web", "/app/index.html"))

    power_opt = MobilePowerOptimizer()
    print("Power Optimization (Low Battery):", power_opt.optimize_inference("qnc_classifier", 15.0))
    print("Power Optimization (High Battery):", power_opt.optimize_inference("qnc_classifier", 85.0))

    ui_adapter = AdaptiveUIAdapter()
    print("Adaptive UI (Tablet):", ui_adapter.adjust_layout(1024, 768, "tablet"))
    print("Adaptive UI (Phone):", ui_adapter.adjust_layout(390, 844, "phone"))
