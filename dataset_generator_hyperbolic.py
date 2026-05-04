# dataset_generator_hyperbolic.py
# Arkhe Forge — Geração de Dataset Hierárquico para PoC do Tradutor Hiperbólico
# Objetivo: Criar vetores de 32-d com estrutura taxonômica de 5 níveis.

import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

# --- Parâmetros do Dataset ---
VEC_DIM = 32            # Dimensionalidade final do vetor (Hiperbólico efetivo)
N_SAMPLES = 50000       # Número total de eventos
NOISE_LEVEL = 0.15      # Ruído Gaussiano intra-classe
EOLUS_NOISE_RATIO = 0.1 # Proporção de amostras que serão "fantasmas" (ruído puro)
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# --- 1. Definição da Árvore de Conceitos (Taxonomia) ---
# Vamos criar uma árvore com fator de ramificação ~3, profundidade 4.
# Nós folha representam eventos cinemáticos específicos.
# Exemplo:
# Nível 0: Raiz (Todo o Universo)
# Nível 1: Cinemático vs. Estático vs. Ambiental
# Nível 2: Cinemático -> Veículo, Humano, Animal
# Nível 3: Veículo -> Carro, Moto, Caminhão
# Nível 4: Carro -> Acelerando, Freando, Virando

taxonomy = {
    "name": "root",
    "children": [
        {
            "name": "kinematic",
            "children": [
                {"name": "vehicle", "children": [
                    {"name": "car", "children": [
                        {"name": "accelerating", "leaf": True},
                        {"name": "braking", "leaf": True},
                        {"name": "turning", "leaf": True}
                    ]},
                    {"name": "motorcycle", "leaf": True},
                    {"name": "truck", "leaf": True}
                ]},
                {"name": "human", "leaf": True},
                {"name": "animal", "leaf": True}
            ]
        },
        {
            "name": "static",
            "children": [
                {"name": "building", "leaf": True},
                {"name": "vegetation", "leaf": True}
            ]
        },
        {
            "name": "ambiental", # Será usado para injetar os "fantasmas de Éolo"
            "leaf": True,
            "is_eolus": True
        }
    ]
}

# --- 2. Função para Gerar Centroides por Classe ---
def generate_centroids(tree, parent_centroid=None, depth=0):
    centroids = {}
    if parent_centroid is None:
        # Raiz na "origem" do espaço
        parent_centroid = np.zeros(VEC_DIM)

    # Calcula um deslocamento para cada filho. Quanto mais profundo, maior o ângulo de separação.
    angle_scale = 0.8 + 0.5 * depth
    for i, child in enumerate(tree["children"]):
        # Gera um vetor de direção única para esta classe
        # Usando uma seed baseada no nome para reprodutibilidade
        np.random.seed(hash(child["name"]) % 2**32)
        direction = np.random.randn(VEC_DIM)
        direction = direction / np.linalg.norm(direction)

        # A norma do deslocamento é controlada para que classes mais específicas (profundas)
        # se afastem mais da origem, mimetizando a borda do disco de Poincaré.
        # Para raiz, norma ~ 1.0; para folhas profundas, norma ~ 3.0-4.0
        norm_offset = 0.8 + depth * 1.5
        child_centroid = parent_centroid + direction * norm_offset

        centroids[child["name"]] = child_centroid

        if "children" in child:
            # Recursão
            child_centroids = generate_centroids(child, child_centroid, depth + 1)
            centroids.update(child_centroids)

    return centroids

# Gerar os centroides
print("[ARKHE] Gerando topologia hiperbólica do dataset...")
centroids = generate_centroids({"children": taxonomy["children"]})

# Adicionar a raiz explicitamente
centroids["root"] = np.zeros(VEC_DIM)

# --- 3. Gerar Amostras com Ruído Intra-Classe ---
data = []
labels = []
eolus_indices = []

# Para cada nó folha, gerar múltiplas amostras
leaf_nodes = ["accelerating", "braking", "turning", "motorcycle", "truck",
              "human", "animal", "building", "vegetation"]

samples_per_leaf = N_SAMPLES // len(leaf_nodes)

for leaf in leaf_nodes:
    centroid = centroids[leaf]
    # Gerar amostras ao redor do centroide com ruído Gaussiano
    samples = np.random.randn(samples_per_leaf, VEC_DIM) * NOISE_LEVEL + centroid
    data.append(samples)
    labels.extend([leaf] * samples_per_leaf)

data = np.vstack(data)
labels = np.array(labels)

# --- 4. Injetar os "Fantasmas de Éolo" (Ruído Ambiental) ---
n_eolus = int(N_SAMPLES * EOLUS_NOISE_RATIO)
# Os fantasmas são ruído Gaussiano puro, centrado na origem do hiperboloide (norma pequena)
eolus_samples = np.random.randn(n_eolus, VEC_DIM) * 0.2  # Norma muito baixa
eolus_labels = ["eolus_phantom"] * n_eolus

data = np.vstack([data, eolus_samples])
labels = np.concatenate([labels, eolus_labels])

# Embaralhar
indices = np.random.permutation(len(data))
data = data[indices]
labels = labels[indices]

print(f"[ARKHE] Dataset gerado: {len(data)} amostras de dimensão {VEC_DIM}")
print(f"Distribuição de classes: {np.unique(labels, return_counts=True)}")

# --- 5. Validação Visual da Topologia (Projeção PCA e t-SNE) ---
print("[ARKHE] Projetando dados para validação visual...")
# Redução de dimensionalidade para 2D (apenas para visualização, não para treino)
pca = PCA(n_components=2)
data_2d_pca = pca.fit_transform(data)

tsne = TSNE(n_components=2, perplexity=30, max_iter=1000, random_state=RANDOM_SEED)
data_2d_tsne = tsne.fit_transform(data)

# Plotagem
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Mapa de cores para as classes
unique_labels = np.unique(labels)
colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
color_map = {label: colors[i] for i, label in enumerate(unique_labels)}

for label in unique_labels:
    idx = labels == label
    axes[0].scatter(data_2d_pca[idx, 0], data_2d_pca[idx, 1],
                    c=[color_map[label]], label=label, alpha=0.6, s=5)
    axes[1].scatter(data_2d_tsne[idx, 0], data_2d_tsne[idx, 1],
                    c=[color_map[label]], label=label, alpha=0.6, s=5)

axes[0].set_title("Projeção PCA do Dataset Hierárquico")
axes[0].legend(markerscale=3, fontsize='small', loc='upper right')
axes[1].set_title("Projeção t-SNE do Dataset Hierárquico")
axes[1].legend(markerscale=3, fontsize='small', loc='upper right')

plt.tight_layout()
plt.savefig("hyperbolic_dataset_validation.png", dpi=150)
print("[ARKHE] Visualização salva como 'hyperbolic_dataset_validation.png'.")

# Salvar o dataset para uso no treinamento
np.savez("tau_hyperbolic_poc_dataset.npz", data=data, labels=labels)
print("[ARKHE] Dataset salvo como 'tau_hyperbolic_poc_dataset.npz'.")
