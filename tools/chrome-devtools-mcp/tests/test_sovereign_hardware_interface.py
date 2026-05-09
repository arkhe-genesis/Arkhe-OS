import pytest
from core.hardware.sovereign_hardware_interface import (
    Substrate123_SovereignHardwareInterface,
    SovereignHardwareCompiler,
    HardwareTarget,
    PLANKCeremonyDescription,
    Modality,
    OptimizationGoal,
    MercyConstraints,
    FakeFormalVerifier
)

class FullFakeFormalVerifier(FakeFormalVerifier):
    def prove_performance(self, kernel, goal):
        class Perf:
            def __init__(self):
                self.meets_deadline = True
                self.predicted_latency = 100
        return Perf()
    def prove_safety(self, kernel, invariants):
        class Safety:
            def __init__(self):
                self.all_invariants_preserved = True
                self.violated_invariants = []
        return Safety()

def test_compile_ceremony():
    hardware = HardwareTarget(compute_capability="sm_80", sm_registers=65536, warps_per_sm=64)
    compiler = SovereignHardwareCompiler(model_weights="fake_path", hardware_spec=hardware)

    ceremony = PLANKCeremonyDescription(
        ceremony="pdi_computation",
        modalities=[Modality(name="eeg")],
        hardware_target=hardware,
        optimization_goal=OptimizationGoal(latency_us_target=500, power_mw_limit=200000),
        mercy_constraints=MercyConstraints(mercy_gap_floor=0.04, epsilon_bounds=[0.01, 0.05])
    )

    kernel = compiler.compile_ceremony(ceremony)
    assert kernel.ptx_code.startswith("// Symbolic annotation for pdi_computation")
    assert kernel.sass_hash is not None
    assert kernel.warp_schedule.warps == 64

def test_substrate123():
    hardware = HardwareTarget(compute_capability="sm_80", sm_registers=65536, warps_per_sm=64)
    compiler = SovereignHardwareCompiler(model_weights="fake_path", hardware_spec=hardware)
    verifier = FullFakeFormalVerifier()

    substrate = Substrate123_SovereignHardwareInterface(compiler=compiler, verifier=verifier)

    assert substrate.substrate_id == 123
    assert substrate.compiler_model == "ARKHE-CUDA-LLM-v∞.Ω.∇+++.12"
    assert "pdi_computation" in substrate.ceremony_kernels

    ceremony = PLANKCeremonyDescription(
        ceremony="zk_stark_prover",
        modalities=[Modality(name="zkp")],
        hardware_target=hardware,
        optimization_goal=OptimizationGoal(latency_us_target=50000, power_mw_limit=250000),
        mercy_constraints=MercyConstraints(mercy_gap_floor=0.04, epsilon_bounds=[0.01, 0.05])
    )

    verified_kernel = substrate.compile_and_verify(ceremony)
    assert verified_kernel.load_address == 0x10000000
    assert verified_kernel.kernel.ptx_code.startswith("// Symbolic annotation for zk_stark_prover")

    # Test execute_with_feedback loop
    result = substrate.execute_with_feedback(verified_kernel, b"input_data")
    assert result.latency_us == 150
    assert result.power_mw == 120
    assert result.mercy_gap_preserved is True
