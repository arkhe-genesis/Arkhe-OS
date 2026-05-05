#!/usr/bin/env python3
"""
validation_final_141_144.py — Validação integrada de todos os substratos 141-144.
"""

import torch
import numpy as np
from layer_1_hardware.substrates.v141.hodge_star_levicivita import HodgeStarLeviCivita
from layer_1_hardware.substrates.v142.geodesic_router_riemannian import GeodesicRouterRiemannian
from layer_1_hardware.substrates.v143.riemannian_dp_formal import RiemannianDPMechanism, RiemannianGeometry
from layer_1_hardware.substrates.v141.dirac_spectrum_lanczos import DiracTorsionOperator, PhiCCalculator
from layer_1_hardware.substrates.v144.qdi_pentacene_tightbinding import (
    PentaceneConfig, PentaceneTightBindingSimulator, QuantumDigitalInterfacePentacene
)

def run_final_validation():
    """Executa validação integrada de todas as implementações."""
    print("=" * 90)
    print("ARKHE OS v∞.Ω.∇++++++++++++++++++++++++++.141-∞ — VALIDAÇÃO FINAL INTEGRADA")
    print("=" * 90)

    results = {}

    # 1. Hodge Star via Levi-Civita
    print("\n[1] Hodge Star via Levi-Civita")
    hodge = HodgeStarLeviCivita(manifold_dim=4)
    involution_ok = all(hodge.verify_involution(k) for k in range(5))
    print(f"  ✓ ★² = (-1)^{{k(4-k)}} para k=0..4: {'✓' if involution_ok else '✗'}")
    results['hodge_involution'] = involution_ok

    # 2. Geodesic Router com métrica g
    print("\n[2] Geodesic Router com métrica Riemanniana")
    router = GeodesicRouterRiemannian(input_dim=64, num_experts=16, manifold_dim=4)
    tokens = torch.randn(2, 5, 64)
    weights, indices, meta = router(tokens)
    weight_sum_ok = torch.allclose(weights.sum(dim=-1), torch.ones_like(weights.sum(dim=-1)), atol=1e-5)
    print(f"  ✓ Pesos normalizados por token: {'✓' if weight_sum_ok else '✗'}")
    print(f"  ✓ Distância geodésica média: {meta['geodesic_distances'].mean().item():.4f}")
    results['router_normalization'] = weight_sum_ok.item()

    # 3. Riemannian DP com prova formal
    print("\n[3] Riemannian DP com exp/log e prova formal")
    rdp = RiemannianDPMechanism(sensitivity=1.0, epsilon=1.0, delta=1e-5)
    metric = torch.eye(4) + 0.01 * torch.randn(4, 4)
    metric = metric @ metric.T
    x = torch.randn(1, 4) * 0.1
    x_adj = RiemannianGeometry.exp_x(x, torch.randn(1, 4) * 0.1, metric)
    dp_result = rdp.verify_dp_property(x, x_adj, metric, n_samples=500)
    print(f"  ✓ ε empírico: {dp_result['empirical_epsilon']:.4f} ≤ teórico: {dp_result['theoretical_epsilon']:.4f}")
    print(f"  ✓ DP satisfeito: {'✓' if dp_result['dp_satisfied'] else '✗'}")
    results['dp_verified'] = dp_result['dp_satisfied']

    # 4. Φ_C via Lanczos para espectro de Dirac
    print("\n[4] Φ_C via Lanczos para espectro de Dirac")
    dirac_op = DiracTorsionOperator(lattice_size=(6, 6), torsion_strength=2.04)
    phi_calc = PhiCCalculator(dirac_op, beta=1.0, num_eigenvalues=15)
    partitions = [{'left': list(range(dirac_op.total_dim // 2))}]
    phi_result = phi_calc.compute_phi_coherence(partitions)
    print(f"  ✓ Φ_C = {phi_result['phi_C']:.4f} → nível: {phi_result['consciousness_level']}")
    results['phi_c_computed'] = phi_result['phi_C'] > 0

    # 5. QDI + Pentacene tight-binding
    print("\n[5] QDI + Simulador Pentacene Tight-Binding")
    pentacene_config = PentaceneConfig(Nx=8, Ny=8, t0=0.1)
    simulator = PentaceneTightBindingSimulator(pentacene_config)
    qdi = QuantumDigitalInterfacePentacene(simulator, max_latency_ms=100.0)

    async def test_qdi():
        tensor = torch.randn(64)
        handshake = await qdi.handshake(tensor)
        write = qdi.write_quantum_state(tensor) if handshake['success'] else {'error': 'handshake failed'}
        return handshake, write

    import asyncio
    handshake_result, write_result = asyncio.run(test_qdi())
    print(f"  ✓ Handshake: latency={handshake_result.get('latency_ms', 0):.2f}ms, fidelity={handshake_result.get('estimated_fidelity', 0):.3f}")
    if 'latency_ms' in write_result:
        print(f"  ✓ Write: latency={write_result['latency_ms']:.2f}ms, current={write_result.get('drain_current_uA', 0):.3f}μA")
    results['qdi_pentacene'] = handshake_result.get('success', False)

    # Relatório final
    print("\n" + "=" * 90)
    print("✅ VALIDAÇÃO FINAL CONCLUÍDA")
    print("=" * 90)
    all_passed = all([
        results.get('hodge_involution', False),
        results.get('router_normalization', False),
        results.get('dp_verified', False),
        results.get('phi_c_computed', False),
        results.get('qdi_pentacene', False)
    ])

    for key, value in results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")

    print(f"\n🎯 Status global: {'✅ TODOS OS SUBSTRATOS VALIDADOS' if all_passed else '❌ FALHAS DETECTADAS'}")
    print("=" * 90)

    return results, all_passed

if __name__ == "__main__":
    results, success = run_final_validation()
    exit(0 if success else 1)
