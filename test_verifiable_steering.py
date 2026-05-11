#!/usr/bin/env python3
"""
test_verifiable_steering.py
Teste unitário para VerifiableManifoldSteerer com dados sintéticos.
"""
import numpy as np
from sklearn.decomposition import PCA
from verifiable_manifold_steering import VerifiableManifoldSteerer

def test_steering_basic():
    """Teste básico de steering com manifold sintético."""
    print("🧭 Testing VerifiableManifoldSteerer...")

    # Gerar manifold sintético (círculo em 2D)
    n_points = 200
    t = np.linspace(0, 2*np.pi, n_points)
    manifold_2d = np.column_stack([np.cos(t), np.sin(t)])  # Círculo unitário

    # Adicionar ruído pequeno
    manifold_noisy = manifold_2d + np.random.randn(n_points, 2) * 0.05

    # Preparar dados do manifold
    crystals = list(range(50))  # Mock: 50 cristais associados
    pca = PCA(n_components=2)
    pca.fit(manifold_noisy)

    manifold_data = {
        'points': manifold_noisy,
        'crystals': crystals,
        'embedding': pca
    }

    # Inicializar steerer
    steerer = VerifiableManifoldSteerer(
        manifold_data,
        smoothness_threshold=0.1,
        max_step_size=0.05,
        verification_epsilon=0.01
    )

    # Definir intenções de teste (projeções no espaço latente)
    start_intention = np.array([1.0, 0.0])  # Ponto no círculo
    end_intention = np.array([0.0, 1.0])    # Outro ponto

    # Executar steering
    result = steerer.steer_with_verification(
        start_intention, end_intention, n_steps=20, generate_proof=False  # Mock: sem prova real
    )

    # Validar trajetória
    path_latent = np.array(result['path_latent'])
    assert path_latent.shape == (20, 2), f"Wrong path shape: {path_latent.shape}"

    # Verificar suavidade (curvatura)
    max_curvature = result['smoothness_metrics']['max_curvature']
    assert max_curvature < steerer.smoothness_threshold * 2, \
        f"Curvature {max_curvature:.4f} exceeds threshold"

    # Verificar erro de reconstrução (mock: sempre pequeno para dados sintéticos)
    recon_error = result['smoothness_metrics']['reconstruction_error']
    assert recon_error < 0.1, f"Reconstruction error {recon_error:.4f} too high"

    print(f"   ✓ Path generated: {path_latent.shape}, curvature={max_curvature:.4f}")

    # Testar com prova (mock: validar estrutura da saída)
    result_with_proof = steerer.steer_with_verification(
        start_intention, end_intention, n_steps=20, generate_proof=True
    )

    if result_with_proof['proof']:
        proof = result_with_proof['proof']
        required_proof_fields = ['proof_hash', 'path_length', 'smoothness_verified',
                                 'reconstruction_epsilon', 'manifold_crystals']
        for field in required_proof_fields:
            assert field in proof, f"Missing proof field: {field}"
        print("   ✓ Proof structure validation OK")

    print("✅ VerifiableManifoldSteerer unit tests PASSED")
    return True

if __name__ == '__main__':
    test_steering_basic()
