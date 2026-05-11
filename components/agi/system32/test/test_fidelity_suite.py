#!/usr/bin/env python3
# test_fidelity_suite.py — Suite de Testes de Fidelidade para RCP v2.0
# ARKHE OS — Substrate 315: Automated Coherence Validation

import unittest
import numpy as np
from scipy import stats
import hashlib
import time
import sys
import os

# Adicionar caminho para módulos AGI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime', 'quantum'))

from rcp_v2_engine import RetrocausalChannel8Bit, QHTTPRetrocausalTransport


class TestRetrocausalChannelBasic(unittest.TestCase):
    """Testes básicos do canal retrógrado."""

    def setUp(self):
        """Configurar canal para testes."""
        self.channel = RetrocausalChannel8Bit(
            N_ctc=4, N_mec=5, omega_tc=5.0, omega_m=1.0,
            g1=0.8, g2=0.08, T_eff=0.5
        )

    def test_bit_transmission_fidelity(self):
        """Testar fidelidade de transmissão bit a bit."""
        test_cases = [
            (0, "bit_0"),
            (1, "bit_1"),
        ]

        for bit, description in test_cases:
            with self.subTest(description=description):
                # Transmitir bit com múltiplos shots
                weak_values = []
                for _ in range(50):  # n_shots
                    x_w = self.channel.encode_bit(bit, t_weak=0.5, t_post=1.5)
                    weak_values.append(x_w)

                # Decodificar
                mean_xw = np.mean(weak_values)
                decoded = 0 if mean_xw > 0 else 1

                # Verificar fidelidade
                self.assertEqual(decoded, bit,
                               f"Bit {bit} decoded as {decoded}, mean weak value: {mean_xw:.3f}")

    def test_byte_transmission_fidelity(self):
        """Testar fidelidade de transmissão byte a byte."""
        test_bytes = [0x00, 0xFF, 0x55, 0xAA, 0x12, 0x34, 0x78, 0x9B, 0xA7]

        for byte_val in test_bytes:
            with self.subTest(byte=f"0x{byte_val:02x}"):
                decoded, fidelity = self.channel.transmit_byte(
                    byte_val, n_shots=40, t_weak=0.5, t_post=1.5
                )

                # Verificar decodificação correta
                self.assertEqual(decoded, byte_val,
                               f"Byte 0x{byte_val:02x} decoded as 0x{decoded:02x}")

                # Verificar fidelidade mínima
                self.assertGreaterEqual(fidelity, 0.8,
                                      f"Fidelity {fidelity:.2%} below threshold for 0x{byte_val:02x}")

    def test_weak_value_statistics(self):
        """Testar estatísticas de weak values para diferentes bits."""
        # Coletar weak values para bit 0
        wv_0 = [self.channel.encode_bit(0) for _ in range(100)]
        # Coletar weak values para bit 1
        wv_1 = [self.channel.encode_bit(1) for _ in range(100)]

        # Verificar que as distribuições são separáveis
        mean_0 = np.mean(wv_0)
        mean_1 = np.mean(wv_1)
        std_0 = np.std(wv_0)
        std_1 = np.std(wv_1)

        # Teste t para verificar separação estatística
        t_stat, p_value = stats.ttest_ind(wv_0, wv_1)

        self.assertLess(p_value, 0.01,
                       f"Weak value distributions not significantly different (p={p_value:.3f})")
        self.assertGreater(abs(mean_0 - mean_1), 0.3,
                          f"Mean separation too small: |{mean_0:.3f} - {mean_1:.3f}|")


class TestQHTTPIntegration(unittest.TestCase):
    """Testes de integração com protocolo qhttp://."""

    def setUp(self):
        """Configurar transporte qhttp:// para testes."""
        self.channel = RetrocausalChannel8Bit()
        self.transport = QHTTPRetrocausalTransport("TEST-NODE-01", self.channel)

    def test_packet_serialization_roundtrip(self):
        """Testar serialização/deserialização de pacotes qhttp://."""
        original_payload = b"ARKHE"

        packet = self.transport.send_retrocausal_byte(
            "TEST-NODE-02", original_payload[0], n_shots=30
        )

        # Serializar
        serialized = packet.serialize()

        # Deserializar
        deserialized = type(packet).deserialize(serialized)

        # Verificar integridade
        self.assertEqual(deserialized.payload, packet.payload)
        self.assertEqual(deserialized.src_node, packet.src_node)
        self.assertEqual(deserialized.dst_node, packet.dst_node)
        self.assertEqual(deserialized.retrocausal_signature, packet.retrocausal_signature)

    def test_message_transmission_integrity(self):
        """Testar integridade de transmissão de mensagem completa."""
        test_message = "ARKHE OS"

        # Enviar mensagem
        packets = self.transport.send_retrocausal_message(
            "TEST-NODE-02", test_message, n_shots=25
        )

        # Verificar número de pacotes
        self.assertEqual(len(packets), len(test_message.encode('utf-8')))

        # Verificar integridade de cada byte
        for i, (packet, expected_byte) in enumerate(zip(packets, test_message.encode('utf-8'))):
            self.assertEqual(packet.payload[0], expected_byte,
                           f"Byte {i} mismatch: expected 0x{expected_byte:02x}, got 0x{packet.payload[0]:02x}")

    def test_coherence_verification_flag(self):
        """Testar flag de verificação de coerência em pacotes."""
        # Transmitir com alta fidelidade
        packet_high = self.transport.send_retrocausal_byte(
            "TEST-NODE-02", 0xA7, n_shots=100  # Muitos shots para alta fidelidade
        )

        # Transmitir com baixa fidelidade (poucos shots)
        packet_low = self.transport.send_retrocausal_byte(
            "TEST-NODE-02", 0xA7, n_shots=5  # Poucos shots para baixa fidelidade
        )

        # Verificar flags de coerência
        self.assertTrue(packet_high.coherence_verified,
                       "High-fidelity packet should have coherence_verified=True")
        # Nota: packet_low.coherence_verified pode ser True ou False dependendo do ruído
        # O importante é que o sistema tente verificar


class TestFidelityThresholds(unittest.TestCase):
    def setUp(self):
        self.channel = RetrocausalChannel8Bit()
    """Testes de thresholds de fidelidade e parâmetros do sistema."""

    def test_shots_per_bit_impact(self):
        """Testar impacto de shots por bit na fidelidade."""
        byte_val = 0xA7
        shot_counts = [10, 25, 50, 100]
        fidelities = []

        for n_shots in shot_counts:
            _, fidelity = self.channel.transmit_byte(
                byte_val, n_shots=n_shots, t_weak=0.5, t_post=1.5
            )
            fidelities.append(fidelity)

        # Verificar tendência: mais shots → maior fidelidade (em média)
        # Nota: devido ao ruído estocástico, testamos com múltiplas execuções
        avg_fidelities = []
        for n_shots in shot_counts:
            fids = []
            for _ in range(5):  # Múltiplas execuções para média
                _, fid = self.channel.transmit_byte(byte_val, n_shots=n_shots)
                fids.append(fid)
            avg_fidelities.append(np.mean(fids))

        # Verificar que fidelidade média aumenta com shots (tendência geral)
        self.assertGreaterEqual(avg_fidelities[-1], avg_fidelities[0],
                          "Fidelity should generally increase with more shots")

    def test_temporal_window_impact(self):
        """Testar impacto da janela temporal na fidelidade."""
        byte_val = 0xA7
        temporal_configs = [
            (0.3, 1.0, "short_window"),
            (0.5, 1.5, "medium_window"),  # Padrão
            (0.8, 2.5, "long_window"),
        ]

        fidelities = []
        for t_weak, t_post, desc in temporal_configs:
            with self.subTest(window=desc):
                _, fidelity = self.channel.transmit_byte(
                    byte_val, n_shots=40, t_weak=t_weak, t_post=t_post
                )
                fidelities.append(fidelity)

                # Verificar fidelidade mínima aceitável
                self.assertGreaterEqual(fidelity, 0.7,
                                      f"Fidelity {fidelity:.2%} below minimum for {desc}")

        # Verificar que janela muito curta ou muito longa pode degradar performance
        # (teste qualitativo - em produção, calibrar parâmetros ótimos)


class TestSystemIntegration(unittest.TestCase):
    """Testes de integração com o sistema AGI completo."""

    @unittest.skipIf(os.getenv("SKIP_INTEGRATION_TESTS"), "Integration tests disabled")
    def test_ffi_bridge_integration(self):
        """Testar integração com ponte FFI C↔Python."""
        try:
            import ctypes

            # Carregar biblioteca compartilhada
            lib = ctypes.CDLL("/usr/lib/agi_rcp_bridge.so")

            # Definir assinatura da função
            lib.rcp_transmit_byte.argtypes = [
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ubyte,
                ctypes.c_double, ctypes.c_double, ctypes.c_int,
                ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_double)
            ]
            lib.rcp_transmit_byte.restype = ctypes.c_int

            # Preparar buffers de saída
            decoded = ctypes.c_ubyte()
            fidelity = ctypes.c_double()

            # Chamar função via FFI
            result = lib.rcp_transmit_byte(
                b"TEST-SRC", b"TEST-DST", 0xA7,
                0.5, 1.5, 40,
                ctypes.byref(decoded), ctypes.byref(fidelity)
            )

            # Verificar resultado
            self.assertEqual(result, 0, "FFI call failed")
            self.assertEqual(decoded.value, 0xA7, "Byte mismatch via FFI")
            self.assertGreaterEqual(fidelity.value, 0.7, "Fidelity too low via FFI")

        except OSError as e:
            self.skipTest(f"FFI library not available: {e}")

    @unittest.skipIf(os.getenv("SKIP_INTEGRATION_TESTS"), "Integration tests disabled")
    def test_kernel_driver_stub(self):
        """Testar stub do driver kernel (se disponível)."""
        import os

        device_path = "/dev/agi_rcp"
        if not os.path.exists(device_path):
            self.skipTest(f"Device {device_path} not available")

        # Testar abertura do dispositivo
        try:
            fd = os.open(device_path, os.O_RDWR)
            os.close(fd)
            self.assertTrue(True, "Device opened successfully")
        except OSError as e:
            self.fail(f"Failed to open device: {e}")


def run_test_suite(verbose=False):
    """Executar suite completa de testes."""
    # Configurar loader
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    # Configurar runner
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    # Relatório final
    print("\n" + "="*70)
    print("📊 RELATÓRIO FINAL DE TESTES DE FIDELIDADE")
    print("="*70)
    print(f"Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️  Erros: {len(result.errors)}")

    if result.failures:
        print("\n❌ Falhas detalhadas:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n⚠️  Erros detalhados:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('Error:')[-1].strip()}")

    # Retornar código de saída apropriado
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ARKHE OS — Suite de Testes de Fidelidade RCP v2.0")
    parser.add_argument("-v", "--verbose", action="store_true", help="Output verboso")
    parser.add_argument("--skip-integration", action="store_true",
                       help="Pular testes de integração com sistema")

    args = parser.parse_args()

    if args.skip_integration:
        os.environ["SKIP_INTEGRATION_TESTS"] = "1"

    exit_code = run_test_suite(verbose=args.verbose)
    sys.exit(exit_code)
