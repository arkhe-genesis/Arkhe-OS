import pytest
import numpy as np
from integration.neurogenetic_experimental_pipeline import NeurogeneticExperimentalPipeline, ExperimentalConfig
from hardware.optogenetics_platform_adapter import OptogeneticHardware
from models.nonlinear_grn_simulator import GRNInteraction, InteractionType
import json

@pytest.mark.asyncio
async def test_substrato_198_f_pipeline():
    config = ExperimentalConfig(
        rnaseq_data_dir="/tmp/test_rnaseq",
        reference_studies=[],
        hardware_type="dmd_projector",
        wavelength_nm=470.0,
        max_power_mw_mm2=5.0,
        semantic_term="memory_consolidation",
        target_genes={"CREB1": 0.95, "FOS": 0.88},
        grn_interactions=[
            GRNInteraction("external_signal", "CREB1", InteractionType.ACTIVATION, 0.8, hill_coefficient=2.0)
        ],
        duration_hours=24.0,
        sampling_interval_minutes=60.0,
        safety_limits={"max_irradiance_mw_mm2": 10.0}
    )
    pipeline = NeurogeneticExperimentalPipeline(config=config)
    field_3d = np.ones((10, 10, 10, 3))
    result = await pipeline.run_experiment(field_3d=field_3d, replicate=1)

    assert result is not None
    assert result.semantic_term == "memory_consolidation"
    assert result.alignment_score >= 0.0 and result.alignment_score <= 1.0
    assert result.reproducibility_score >= 0.0 and result.reproducibility_score <= 1.0
