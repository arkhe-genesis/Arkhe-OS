#!/usr/bin/env python3
# =========================================================
# Iniciar Simulador de Rede Mesh
# =========================================================
import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mesh.mesh_network import MeshNetwork
from mesh.smartphone_node import ParticleType

def main():
    print("=" * 70)
    print("ARKHE OS - SIMULADOR DE REDE MESH MUNDIAL (Substrato 397)")
    print("=" * 70)

    # Criar rede com 1000 nodos
    mesh = MeshNetwork(n_nodes=1000, world_coverage=True)

    # Simular 100 raios cosmicos
    for i in range(100):
        particle = random.choice([
            ParticleType.MUON, ParticleType.ELECTRON,
            ParticleType.PHOTON, ParticleType.ALPHA
        ])
        mesh.simulate_cosmic_ray(particle, affected_area_km2=random.uniform(50, 200))

    stats = mesh.statistics()

    print(f"\nRede: {stats['n_nodes']} nodos")
    print(f"Eventos detetados: {stats['total_events_detected']}")
    print(f"Eventos partilhados: {stats['total_events_shared']}")
    print(f"Chuveiros coincidentes: {stats['coincident_showers']}")
    print(f"Media eventos/chuveiro: {stats['avg_events_per_shower']:.1f}")
    print(f"Cobertura estimada: {stats['network_coverage_km2']:.2f} km^2")
    print(f"Phi_C da rede: {stats['phi_c']:.4f}")

    # Estimar direcao do primeiro chuveiro
    if mesh.coincident_events:
        direction = mesh.estimate_direction(mesh.coincident_events[0])
        if direction:
            print(f"\nDirecao estimada (primeiro chuveiro):")
            print(f"  dx={direction[0]:.3f}, dy={direction[1]:.3f}, dz={direction[2]:.3f}")

if __name__ == "__main__":
    main()
