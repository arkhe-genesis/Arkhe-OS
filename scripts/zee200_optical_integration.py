#!/usr/bin/env python3
"""
zee200_optical_integration.py
Integra geração de hash ZEE200 real no circuito de watermarking óptico.
"""
import numpy as np
from pathlib import Path
import hashlib

# Import do backend ZEE200 (via pybind11 binding)
# Nota: Requer compilação do backend C++ ZEE200
try:
    import zee200_backend  # Binding pybind11 para ZEE200 C++
    ZEE200_AVAILABLE = True
except ImportError:
    print("⚠️  ZEE200 backend not available — using SHA-256 proxy")
    ZEE200_AVAILABLE = False

class ZEE200OpticalWatermarker:
    """Gera watermark óptico usando hash ZEE200 real."""

    def __init__(self, security_bits=80, zee200_profile=(1, 2, 1, 2)):
        """Inicializa watermarker com parâmetros ZEE200."""
        self.security_bits = security_bits
        self.zee200_profile = zee200_profile

        if ZEE200_AVAILABLE:
            # Inicializar backend ZEE200 real
            self.zee200 = zee200_backend.ZEE200Prover(
                security_bits=security_bits,
                profile=zee200_profile
            )
        else:
            # Fallback: usar SHA-256 como proxy para desenvolvimento
            self.zee200 = None

    def generate_proof(self, statement: dict, witness: dict) -> dict:
        """Gera prova ZEE200 para declaração e testemunha especificadas."""
        if ZEE200_AVAILABLE:
            # Usar backend ZEE200 real
            proof = self.zee200.prove(statement, witness)
            return {
                'hash': proof['proof_hash'],  # 256-bit hash
                'size_bytes': proof['proof_size_bytes'],
                'generation_time_ms': proof['gen_time_ms'],
                'verification_time_ms': proof['verify_time_ms'],
                'post_quantum': proof['post_quantum'],
                'backend': 'zee200_cpp'
            }
        else:
            # Fallback: gerar hash SHA-256 como proxy
            import json
            content = json.dumps({'statement': statement, 'witness': witness}, sort_keys=True)
            hash_bytes = hashlib.sha256(content.encode()).digest()
            return {
                'hash': hash_bytes.hex(),
                'size_bytes': 32,  # SHA-256 output size
                'generation_time_ms': 0.1,  # Approximate
                'verification_time_ms': 0.01,
                'post_quantum': False,
                'backend': 'sha256_proxy'
            }

    def hash_to_spectral_pattern(self, hash_hex: str, epsilon=0.01,
                                wavelength_axis=None, theta_key='arkhe_master_key_2026'):
        """Converte hash ZEE200 em padrão de modulação espectral para watermarking óptico."""
        if wavelength_axis is None:
            wavelength_axis = np.linspace(400, 1550, 1151)  # 400-1550 nm, 1 nm resolution

        # Converter hash hex para bits
        hash_bits = np.array([
            int(bit) for byte in bytes.fromhex(hash_hex)
            for bit in format(byte, '08b')
        ], dtype=int)

        # Gerar padrão de modulação espectral
        modulation = np.ones_like(wavelength_axis)

        for k, bit in enumerate(hash_bits[:256]):  # Usar primeiros 256 bits
            if bit == 1:
                # Frequência espacial ortogonal para cada bit
                f_k = 0.01 + k * 0.001  # Frequências ortogonais
                # Fase inicial derivada da chave secreta
                theta_k = hash(theta_key + str(k)) % (2*np.pi)
                # Adicionar componente de interferência
                modulation += epsilon * np.cos(2*np.pi * f_k * wavelength_axis + theta_k)

        return modulation

    def apply_optical_watermark(self, spectrum_base: np.ndarray,
                               statement: dict, witness: dict,
                               epsilon=0.01) -> tuple:
        """Aplica watermark óptico a espectro base usando prova ZEE200 real."""
        # 1. Gerar prova ZEE200
        proof = self.generate_proof(statement, witness)
        hash_hex = proof['hash']

        # 2. Converter hash em padrão de modulação espectral
        modulation = self.hash_to_spectral_pattern(hash_hex, epsilon)

        # 3. Aplicar modulação ao espectro base
        spectrum_watermarked = spectrum_base * modulation

        return spectrum_watermarked, proof

    def verify_optical_watermark(self, spectrum_measured: np.ndarray,
                                expected_proof: dict,
                                epsilon=0.01, threshold=0.85) -> tuple:
        """Verifica watermark óptico no espectro medido."""
        # Reconstruir padrão de modulação esperado
        modulation_expected = self.hash_to_spectral_pattern(
            expected_proof['hash'], epsilon
        )

        # Correlação cruzada normalizada
        s_norm = (spectrum_measured - np.mean(spectrum_measured)) / np.std(spectrum_measured)
        m_norm = (modulation_expected - np.mean(modulation_expected)) / np.std(modulation_expected)
        correlation = np.corrcoef(s_norm, m_norm)[0, 1]

        # Decisão de verificação
        verified = correlation > threshold

        return verified, float(correlation)

def test_zee200_integration():
    """Teste de integração ZEE200 com watermarking óptico."""
    print("🔐 Testing ZEE200 optical watermarking integration...")

    # Inicializar watermarker
    watermarker = ZEE200OpticalWatermarker()

    # Dados de teste para prova ZEE200
    statement = {
        'circuit_id': 'arkhe_vortex_sensor_v340.2',
        'public_inputs': {'capture_threshold': 0.8, 'security_bits': 80}
    }
    witness = {
        'private_phases': np.random.uniform(0, 2*np.pi, 768).tolist(),
        'manifold_params': {'kappa': 0.843, 'lambda_l1': 0.0041}
    }

    # Gerar prova e aplicar watermark
    spectrum_base = np.ones(1151) * 0.5  # Espectro base simulado
    spectrum_watermarked, proof = watermarker.apply_optical_watermark(
        spectrum_base, statement, witness, epsilon=0.01
    )

    print(f"✓ Proof generated:")
    print(f"   • Hash: {proof['hash'][:16]}...")
    print(f"   • Size: {proof['size_bytes']} bytes")
    print(f"   • Backend: {proof['backend']}")

    # Verificar watermark
    verified, correlation = watermarker.verify_optical_watermark(
        spectrum_watermarked, proof, epsilon=0.01
    )

    print(f"✓ Watermark verification:")
    print(f"   • Verified: {verified}")
    print(f"   • Correlation: {correlation:.4f}")

    # Teste de robustez a ruído
    noise_levels = [0.001, 0.01, 0.05]
    print(f"\n🔍 Testing robustness to noise:")
    for noise in noise_levels:
        spectrum_noisy = spectrum_watermarked + np.random.normal(0, noise, len(spectrum_watermarked))
        verified_noisy, corr_noisy = watermarker.verify_optical_watermark(
            spectrum_noisy, proof, epsilon=0.01
        )
        print(f"   • Noise={noise:.3f}: verified={verified_noisy}, corr={corr_noisy:.4f}")

    print(f"\n✅ ZEE200 optical integration test complete")
    return verified and correlation > 0.9

if __name__ == '__main__':
    success = test_zee200_integration()
    exit(0 if success else 1)
