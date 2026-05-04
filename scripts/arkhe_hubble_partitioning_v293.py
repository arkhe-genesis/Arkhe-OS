import numpy as np
from scipy.spatial import SphericalVoronoi
from typing import List, Dict
import json

# Constantes cosmológicas (ΛCDM Planck 2018)
H0 = 67.4  # km/s/Mpc
C = 299792.458  # km/s
R_HUBBLE_MPC = C / H0  # ~4448 Mpc
V_HUBBLE_GPC3 = (4/3) * np.pi * (R_HUBBLE_MPC / 1000)**3  # ~368.6 Gpc³

def generate_hubble_partitions(n_partitions: int = 1024) -> List[Dict]:
    """
    Gera 1024 partições do volume de Hubble via Spherical Voronoi.
    Cada partição tem volume ~V_Hubble / 1024 ≈ 0.36 Gpc³.
    """
    # Gerar pontos aleatórios na esfera de raio R_Hubble (distribuição uniforme)
    np.random.seed(42)  # Reprodutibilidade
    points = []
    for _ in range(n_partitions):
        # Distribuição uniforme na esfera: cos(θ) uniforme, φ uniforme
        cos_theta = np.random.uniform(-1, 1)
        theta = np.arccos(cos_theta)
        phi = np.random.uniform(0, 2 * np.pi)
        # For SphericalVoronoi, all points must be exactly on the sphere
        r = R_HUBBLE_MPC

        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        points.append([x, y, z])

    points = np.array(points)

    # Criar Voronoi esférico
    sv = SphericalVoronoi(points, radius=R_HUBBLE_MPC, center=[0, 0, 0])
    sv.sort_vertices_of_regions()

    # Calcular propriedades de cada partição
    partitions = []
    for i, region in enumerate(sv.regions):
        vertices = sv.vertices[region]
        if len(vertices) < 3:
            continue

        # Centro da partição (média dos vértices)
        center = np.mean(vertices, axis=0)

        # Raio aproximado (distância máxima do centro a um vértice)
        radius = np.max(np.linalg.norm(vertices - center, axis=1))

        # Volume aproximado (esfera de raio médio)
        volume_gpc3 = (4/3) * np.pi * (radius / 1000)**3

        partitions.append({
            'partition_id': i,
            'center_mpc': center.tolist(),
            'radius_mpc': float(radius),
            'volume_gpc3': float(volume_gpc3),
            'vertex_count': len(vertices),
            'neighbors': []  # Preencher depois com adjacência de Voronoi
        })

    # Calcular adjacência (partições que compartilham arestas no Voronoi)
    # sv.regions gives a list of lists of vertex *indices*, so we just intersect the sets of indices
    for i, region in enumerate(sv.regions):
        for j, other_region in enumerate(sv.regions):
            if i == j:
                continue
            # Duas regiões são vizinhas se compartilham pelo menos 2 vértices
            if len(set(region) & set(other_region)) >= 2:
                partitions[i]['neighbors'].append(j)

    return partitions

# Gerar partições e salvar para configuração dos nós
if __name__ == "__main__":
    partitions = generate_hubble_partitions(1024)

    # Estatísticas
    volumes = [p['volume_gpc3'] for p in partitions]
    print(f"🌌 Partições do Volume de Hubble: {len(partitions)}")
    print(f"   Volume médio: {np.mean(volumes):.3f} Gpc³")
    print(f"   Volume alvo: {V_HUBBLE_GPC3 / 1024:.3f} Gpc³")
    print(f"   Desvio padrão: {np.std(volumes):.3f} Gpc³")
    print(f"   Raio médio das partições: {np.mean([p['radius_mpc'] for p in partitions]):.1f} Mpc")

    with open('hubble_partitions_1024.json', 'w') as f:
        json.dump(partitions, f, indent=2)
    print("✅ Partições salvas em hubble_partitions_1024.json")
