import pytest
import asyncio
from arkhe_edge.edge_ai_optimizer import EdgeModelConfig, EdgeAIOptimizer, QuantizationMode

@pytest.mark.asyncio
async def test_edge_ai_optimizer_hexagon():
    config = EdgeModelConfig(
        model_path="test_model.pt",
        target_device="qualcomm_hexagon",
        quantization_mode=QuantizationMode.MIXED,
        temporal_anchor_enabled=False,
        guardian_validation_enabled=False
    )
    optimizer = EdgeAIOptimizer(config)
    tflite_path = await optimizer.convert_model("test_model.pt")
    assert tflite_path == "test_model.tflite"

    optimized_path = await optimizer.optimize_model(tflite_path)
    assert optimized_path == "test_model_optimized_qualcomm_hexagon.tflite"

    report = await optimizer.validate_model_quality(tflite_path, optimized_path)
    assert report.speedup_factor > 1.0

@pytest.mark.asyncio
async def test_edge_ai_optimizer_apple_ane():
    config = EdgeModelConfig(
        model_path="test_model.pt",
        target_device="apple_ane",
        quantization_mode=QuantizationMode.MIXED,
        temporal_anchor_enabled=False,
        guardian_validation_enabled=False
    )
    optimizer = EdgeAIOptimizer(config)
    tflite_path = await optimizer.convert_model("test_model.pt")
    assert tflite_path == "test_model.tflite"

    optimized_path = await optimizer.optimize_model(tflite_path)
    assert optimized_path == "test_model_optimized_apple_ane.tflite"

    report = await optimizer.validate_model_quality(tflite_path, optimized_path)
    assert report.speedup_factor > 1.0
