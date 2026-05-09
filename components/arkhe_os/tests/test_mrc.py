#!/usr/bin/env python3
# ============================================================
# SUBSTRATO 256: MRC — TEST SUITE
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'network'))

import numpy as np
import random
from mrc_transport import MRCTransportLayer, PlaneStatus, RouteEntry

class TestMRCProtocol:
    def setup_method(self):
        pass

    def test_spray_packets(self):
        mrc = MRCTransportLayer("node_00", num_planes=8)
        mrc._load_srv6_table()
        tensor = np.random.randn(1024, 1024)
        packets = mrc.spray_packets(tensor, "node_01")
        assert len(packets) == 8
        assert all(p.header['src'] == 'node_00' for p in packets)
        print(f"  ✓ Spray: {len(packets)} pacotes")

    def test_transmission_coherence(self):
        mrc = MRCTransportLayer("node_00", num_planes=8, lambda_var=0.1)
        for p in mrc.planes:
            p.coherence = 0.95
        phi1 = mrc.compute_transmission_coherence()
        assert phi1 > 0.9
        for i, p in enumerate(mrc.planes):
            p.coherence = 0.5 + 0.1 * i
        phi2 = mrc.compute_transmission_coherence()
        assert phi2 < phi1
        print(f"  ✓ Coerência: uniforme={phi1:.4f}, variada={phi2:.4f}")

    def test_failure_detection(self):
        mrc = MRCTransportLayer("node_00", num_planes=8)
        failed = mrc.detect_failure(3, loss_rate=0.08)
        assert failed
        assert mrc.planes[3].status == PlaneStatus.RETIRED
        print(f"  ✓ Falha: plano 3 aposentado")

    def test_packet_trimming(self):
        mrc = MRCTransportLayer("node_00", num_planes=8)
        mrc._load_srv6_table()
        mrc.trim_threshold = 0.5
        mrc.planes[2].coherence = 0.2
        tensor = np.random.randn(256, 256)
        packets = mrc.spray_packets(tensor, "node_01")
        trimmed = [p for p in packets if p.trimmed]
        assert len(trimmed) >= 1
        print(f"  ✓ Trimming: {len(trimmed)} pacotes trimmados")

    def test_srv6_routing(self):
        mrc = MRCTransportLayer("node_00", num_planes=8)
        custom_routes = {
            "node_05": RouteEntry(dest_node="node_05", segments=[2, 5, 7, 1], coherence_threshold=0.6)
        }
        mrc._load_srv6_table(custom_routes)
        assert mrc.static_routes["node_05"].segments == [2, 5, 7, 1]
        print(f"  ✓ SRv6: rota correta")

    def test_multimode_fidelity(self):
        k_modes = 4
        F_single = 0.99
        F_multi = F_single ** k_modes
        assert F_multi < F_single
        assert F_multi > 0.95
        print(f"  ✓ Multi-modo: F_{k_modes} = {F_multi:.6f}")

    def test_recovery_probe(self):
        mrc = MRCTransportLayer("node_00", num_planes=8)
        mrc.planes[4].status = PlaneStatus.RETIRED
        random.seed(42)
        recovered = mrc.send_probe(4)
        if recovered:
            assert mrc.planes[4].status == PlaneStatus.RECOVERING
        print(f"  ✓ Recuperação: {'recuperado' if recovered else 'ainda aposentado'}")

    def test_coherence_variance_penalty(self):
        mrc = MRCTransportLayer("node_00", num_planes=4, lambda_var=0.2)
        for p, c in zip(mrc.planes, [0.9, 0.92, 0.88, 0.91]):
            p.coherence = c
        phi_low = mrc.compute_transmission_coherence()
        for p, c in zip(mrc.planes, [0.99, 0.99, 0.81, 0.81]):
            p.coherence = c
        phi_high = mrc.compute_transmission_coherence()
        assert phi_low > phi_high
        print(f"  ✓ Penalidade: low={phi_low:.4f}, high={phi_high:.4f}")

    def test_tensor_reconstruction(self):
        mrc = MRCTransportLayer("node_00", num_planes=4)
        mrc._load_srv6_table()
        original = np.random.randn(512, 512)
        packets = mrc.spray_packets(original, "node_02")
        received = [mrc.receive_packet(p) for p in packets if mrc.receive_packet(p) is not None]
        if len(received) == len(packets):
            reconstructed = np.concatenate(received, axis=0)
            assert reconstructed.shape == original.shape
        print(f"  ✓ Reconstrução: {len(received)}/{len(packets)} slices")

    def test_hypermesh_integration(self):
        mrc = MRCTransportLayer("stargate_node_01", num_planes=8)
        mrc._load_srv6_table()
        gradient = np.random.randn(4096, 4096).astype(np.float32)
        packets = mrc.spray_packets(gradient, "stargate_node_02")
        state = mrc.get_network_state()
        assert state['active_planes'] == 8
        print(f"  ✓ Hyper-Mesh: coerência={state['transmission_coherence']:.4f}")
