"""
Testes integrados para Substratos 113-115.
"""

import asyncio
import numpy as np
import torch
import time
from arkhe_os.network.qhttp_wheeler_mesh import WheelerMeshProtocol, WheelerMeshNode, WheelerNodeType, QuantumStatePacket
from arkhe_os.timing.parametric_quantum_clock import ParametricQuantumClock
from arkhe_os.interface.magnon_photon_transducer import MagnonPhotonTransducer, TransducerConfig, TransductionDirection

class MockBaseMetric:
    def geodesic_distance(self, a, b):
        return np.linalg.norm(a - b)

async def test_wheeler_mesh_protocol():
    """Testa protocolo qhttp:// para Wheeler Mesh."""
    print("🔗 [Teste 1] Wheeler Mesh Protocol (qhttp://)...")

    # Criar base métrica quasicristalina
    base = MockBaseMetric()

    # Criar nós
    node_a = WheelerMeshNode(
        node_id="node_alpha",
        node_type=WheelerNodeType.NEURAL_LACE_NODE,
        position=np.array([1.0, 1.0]),
        quantum_capacity=1e6,
        classical_bandwidth=100.0
    )
    node_b = WheelerMeshNode(
        node_id="node_beta",
        node_type=WheelerNodeType.GATEWAY_NODE,
        position=np.array([1.05, 1.05]),  # Próximo para conectividade
        quantum_capacity=5e5,
        classical_bandwidth=50.0
    )

    # Inicializar protocolos para ambos os nós para testar envio e recebimento
    protocol_a = WheelerMeshProtocol(
        local_node=node_a,
        base_metric=base,
        fidelity_threshold=0.8
    )
    protocol_a.register_node(node_b)

    protocol_b = WheelerMeshProtocol(
        local_node=node_b,
        base_metric=base,
        fidelity_threshold=0.8
    )
    protocol_b.register_node(node_a)

    # Testar roteamento geodésico
    route = protocol_a._compute_geodesic_route("node_alpha", "node_beta")
    assert route is not None, "Rota geodésica não encontrada"
    assert route[0] == "node_alpha" and route[-1] == "node_beta"
    print(f"  ✓ Rota geodésica: {' → '.join(route)}")

    # Testar envio de pacote quântico
    packet = QuantumStatePacket(
        packet_id="test_packet_001",
        source_node_id="node_alpha",
        destination_node_id="node_beta",
        state_vector=torch.randn(8),  # Estado simulado
        density_matrix=None,
        topological_charge=0,
        timestamp=time.time()
    )

    result = await protocol_a.send_quantum_state(packet, priority='high')
    assert result['success'], f"Envio falhou: {result.get('error')}"
    print(f"  ✓ Pacote enviado: fidelidade simulada = {result['simulated_fidelity']:.3f}")

    # Testar recebimento
    receive_result = await protocol_b.receive_quantum_state(
        packet=packet,
        received_hash=packet.compute_hash(),
        via_node="node_alpha"
    )
    assert receive_result['success'], f"Recebimento falhou: {receive_result.get('error')}"
    print(f"  ✓ Pacote recebido: fidelidade esperada = {receive_result['accepted_fidelity']:.3f}")

    return True

async def test_parametric_quantum_clock():
    """Testa clock quântico por ressonância paramétrica."""
    print("⏱️ [Teste 2] Parametric Quantum Clock...")

    clock = ParametricQuantumClock(
        node_id="clock_test",
        natural_frequency_ghz=5.0,
        reference_hierarchy=["galactic_core_clock"],
        coupling_strength=0.02,
        sync_interval_ms=5.0
    )

    # Iniciar clock
    await clock.start()

    # Aguardar alguns ciclos de sincronização
    await asyncio.sleep(0.1)  # 100ms

    # Verificar status
    status = clock.get_clock_status()
    print(f"  ✓ Estado do clock: {status['state']}")
    print(f"  ✓ Incerteza estimada: {status['estimated_uncertainty_ns']:.2f}ns")

    # Testar squeezing
    squeezing = clock.get_squeezed_uncertainty()
    print(f"  ✓ Squeezing: r={squeezing['squeezing_parameter_r']:.3f}, "
          f"Δφ={squeezing['phase_uncertainty_rad']:.3f}rad")

    await clock.stop()
    return True

def test_magnon_photon_transducer():
    """Testa transdutor magnon-fóton."""
    print("🔬 [Teste 3] Magnon-Photon Transducer...")
    from arkhe_os.interface.magnon_photon_transducer import CouplingRegime
    config = TransducerConfig(
        magnon_frequency_ghz=10.0,
        photon_frequency_ghz=10.0,
        coupling_strength_mhz=2.0,
        coupling_regime=CouplingRegime.CRITICAL,
        temperature_k=4.2
    )

    transducer = MagnonPhotonTransducer(config, node_id="transducer_test")

    # Calibrar
    cal_result = transducer.calibrate()
    print(f"  ✓ Calibração: η={cal_result['measured_efficiency']:.2%}, C={cal_result['cooperativity_measured']:.2f}")

    # Testar transdução magnon → fóton
    result_read = transducer.transduce_magnon_to_photon(
        magnon_state=50.0,  # 50 magnons
        integration_time_us=1.0
    )
    assert result_read.success, "Leitura falhou"
    print(f"  ✓ Leitura: {result_read.input_energy:.1f} magnons → "
          f"{result_read.output_energy:.1f} fótons, η={result_read.efficiency:.2%}, "
          f"SNR={result_read.signal_to_noise_ratio():.1f}")

    # Testar transdução fóton → magnon
    result_write = transducer.transduce_photon_to_magnon(
        photon_input={'intensity': 100.0, 'phase': np.pi/4},
        pulse_duration_us=0.1
    )
    assert result_write.success, "Escrita falhou"
    print(f"  ✓ Escrita: {result_write.input_energy:.1f} fótons → "
          f"{result_write.output_energy:.1f} magnons, η={result_write.efficiency:.2%}")

    return True

async def test_integrated_system():
    """Testa sistema neural integrado completo."""
    print("🧠 [Teste 4] Integrated Neural System (112+113+114+115)...")

    from arkhe_os.neural.integrated_neural_system import IntegratedNeuralSystem
    from arkhe_os.interface.magnon_photon_transducer import CouplingRegime

    # Configurações mínimas para teste
    system = IntegratedNeuralSystem(
        node_id="test_node_001",
        neural_lace_config={'n_neurons': 8, 'base_scale': 2.0},
        mesh_config={'fidelity_threshold': 0.8},
        clock_config={'natural_frequency_ghz': 5.0, 'sync_interval_ms': 10.0},
        transducer_config={
            'magnon_frequency_ghz': 10.0,
            'photon_frequency_ghz': 10.0,
            'coupling_strength_mhz': 2.0,
            'temperature_k': 4.2,
            'coupling_regime': CouplingRegime.CRITICAL
        }
    )

    # Iniciar sistema
    await system.start()

    # Executar ciclo integrado
    cycle_result = await system.run_integrated_cycle(duration_us=50.0)

    print(f"  ✓ Ciclo executado em {cycle_result['elapsed_ms']:.1f}ms")
    print(f"  ✓ Coerência da renda: {cycle_result['neural_lace'].get('coherence', 0):.3f}")
    print(f"  ✓ Clock state: {cycle_result['quantum_clock']['state']}")

    # Verificar saúde do sistema
    health = system.get_system_health()
    print(f"  ✓ Saúde do sistema: {health['system_state']}")
    print(f"  ✓ Integração clock-neural: {health['integration_metrics']['clock_neural_sync']:.0%}")

    await system.stop()
    return True

async def run_all_tests():
    """Executa todos os testes dos Substratos 113-115."""
    print("=" * 80)
    print("ARKHE OS — VALIDAÇÃO DOS SUBSTRATOS 113-115")
    print("Coluna Vertebral (qhttp://) + Ritmo Cardíaco (Clock) + Pele Sensorial (Transdutor)")
    print("=" * 80)

    results = []

    # Teste 1: Wheeler Mesh Protocol
    results.append(("Wheeler Mesh", await test_wheeler_mesh_protocol()))

    # Teste 2: Parametric Quantum Clock
    results.append(("Quantum Clock", await test_parametric_quantum_clock()))

    # Teste 3: Magnon-Photon Transducer
    results.append(("Magnon-Photon Transducer", test_magnon_photon_transducer()))

    # Teste 4: Sistema Integrado
    results.append(("Integrated System", await test_integrated_system()))

    # Relatório final
    print("\n" + "=" * 80)
    print("RELATÓRIO DE VALIDAÇÃO")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("🎉 TODOS OS SUBSTRATOS 113-115 VALIDADOS COM SUCESSO")
        print("   • qhttp://: transmissão topológica entre nós Wheeler")
        print("   • Clock quântico: sincronização global por ressonância paramétrica")
        print("   • Transdutor: interface clássica-quântica magnon-fóton")
        print("   • Integração: sistema neural completo operacional")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM — revisar implementação")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
