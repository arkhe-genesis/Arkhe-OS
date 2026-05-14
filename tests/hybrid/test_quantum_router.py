#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_quantum_router.py — Testes de validação do roteador híbrido
"""

import pytest
import numpy as np
from src.arkhe.quantum.hybrid.quantum_router import (
    QuantumRouter, CircuitFragment, CircuitFragmentType,
    HybridExecutionConfig, QuantumBackendType
)

class TestQuantumRouter:

    @pytest.fixture
    def router(self):
        """Fixture com roteador configurado para testes."""
        # Mock backends para testes
        class MockPhotonicBackend:
            async def execute(self, config):
                return type('Result', (), {
                    'status': 'completed',
                    'photon_counts': {'00': 512, '11': 512},
                    'interference_visibility': 0.97,
                    'execution_time_ms': 120,
                    'temporal_anchor': 'photonic_anchor_123',
                })()

        class MockIonTrapBackend:
            async def execute(self, config):
                return type('Result', (), {
                    'status': 'completed',
                    'measurement_counts': {'0': 1024},
                    'gate_fidelity': 0.999,
                    'execution_time_ms': 300,
                    'temporal_anchor': 'iontrap_anchor_456',
                })()

        config = HybridExecutionConfig(target_fidelity=0.99)
        return QuantumRouter(
            photonic_backend=MockPhotonicBackend(),
            iontrap_backend=MockIonTrapBackend(),
            config=config,
        )

    @pytest.mark.asyncio
    async def test_fragment_decomposition(self, router):
        """Testar decomposição de circuito QNC em fragmentos."""
        qnc_circuit = {
            'gates': [
                {'type': 'BS', 'target1': 0, 'target2': 1, 'modes': 4},
                {'type': 'MS', 'qubits': [0, 1], 'depth': 5},
                {'type': 'Teleport', 'qubits': [0, 1, 2]},
            ]
        }

        fragments = router._decompose_qnc_circuit(qnc_circuit)

        assert len(fragments) == 3
        assert fragments[0].fragment_type == CircuitFragmentType.BOSON_SAMPLING
        assert fragments[1].fragment_type == CircuitFragmentType.HIGH_FIDELITY_GATE
        assert fragments[2].fragment_type == CircuitFragmentType.ENTANGLEMENT_DIST

    @pytest.mark.asyncio
    async def test_backend_assignment(self, router):
        """Testar atribuição de fragmentos a backends ótimos."""
        fragments = [
            CircuitFragment(
                fragment_id="frag_001",
                circuit_qasm='{"type": "BS"}',
                fragment_type=CircuitFragmentType.BOSON_SAMPLING,
                qubit_count=4,
                depth_estimate=1,
                fidelity_requirement=0.95,
                latency_sensitivity=0.3,
            ),
            CircuitFragment(
                fragment_id="frag_002",
                circuit_qasm='{"type": "MS"}',
                fragment_type=CircuitFragmentType.HIGH_FIDELITY_GATE,
                qubit_count=2,
                depth_estimate=5,
                fidelity_requirement=0.999,
                latency_sensitivity=0.6,
            ),
        ]

        assignments = await router._assign_backends(fragments)

        # Boson sampling deve ir para fotônico
        assert assignments["frag_001"].backend == QuantumBackendType.PHOTONIC
        # High-fidelity gate deve ir para íons
        assert assignments["frag_002"].backend == QuantumBackendType.ION_TRAP

    @pytest.mark.asyncio
    async def test_hybrid_execution_end_to_end(self, router):
        """Teste end-to-end de execução híbrida."""
        qnc_circuit = {
            'gates': [
                {'type': 'BS', 'target1': 0, 'target2': 1, 'modes': 4},
                {'type': 'MS', 'qubits': [0, 1], 'depth': 5},
            ]
        }

        result = await router.route_and_execute(qnc_circuit)

        assert result.success is True
        assert result.estimated_fidelity >= 0.97  # Mínimo esperado
        assert result.execution_time_ms > 0
        assert result.integrity_proof is not None
        assert len(result.integrity_proof) == 16  # Hash hex de 16 chars
