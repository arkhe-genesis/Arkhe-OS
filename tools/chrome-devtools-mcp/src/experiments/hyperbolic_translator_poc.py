import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import json
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from scipy.stats import spearmanr

# --- Hyperbolic Logic (Lorentz Model) ---

def lorentz_product(u, v):
    return torch.sum(u[:, :-1] * v[:, :-1], dim=-1) - u[:, -1] * v[:, -1]

def lorentz_dist(u, v):
    # d(u,v) = acosh(-<u,v>)
    prod = -lorentz_product(u, v)
    return torch.acosh(torch.clamp(prod, min=1.0 + 1e-7))

class ExponentialMap(nn.Module):
    def forward(self, x):
        norm = torch.norm(x, p=2, dim=-1, keepdim=True).clamp(min=1e-7)
        return torch.cat([torch.sinh(norm) * (x / norm), torch.cosh(norm)], dim=-1)

# --- Models ---

class EuclideanModel(nn.Module):
    def __init__(self, in_dim=32, out_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, out_dim)
        )
    def forward(self, x): return self.net(x)

class HyperbolicModel(nn.Module):
    def __init__(self, in_dim=32, out_dim=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, out_dim - 1)
        )
        self.exp = ExponentialMap()
    def forward(self, x): return self.exp(self.net(x))

# --- Task Setup ---

def run_poc():
    print("[ARKHE] Iniciando PoC do Tradutor Hiperbólico v2...")

    # Load Dataset
    dataset = np.load("tau_hyperbolic_poc_dataset.npz")
    X = dataset['data'].astype(np.float32)
    L = dataset['labels']
    unique_labels = np.unique(L)

    # Taxonomy Structure (Tree Distances)
    tax_tree = {
        "accelerating": ["car", "vehicle", "kinematic", "root"],
        "braking": ["car", "vehicle", "kinematic", "root"],
        "turning": ["car", "vehicle", "kinematic", "root"],
        "motorcycle": ["vehicle", "kinematic", "root"],
        "truck": ["vehicle", "kinematic", "root"],
        "human": ["kinematic", "root"],
        "animal": ["kinematic", "root"],
        "building": ["static", "root"],
        "vegetation": ["static", "root"],
        "eolus_phantom": ["ambiental", "root"]
    }

    taxonomy_distances = {}
    for l1 in unique_labels:
        for l2 in unique_labels:
            if l1 == l2:
                taxonomy_distances[(l1, l2)] = 0.0
                continue
            p1 = [l1] + tax_tree[l1]
            p2 = [l2] + tax_tree[l2]
            common = next(node for node in p1 if node in p2)
            dist = p1.index(common) + p2.index(common)
            taxonomy_distances[(l1, l2)] = float(dist)

    # Split
    X_train, X_test, L_train, L_test = train_test_split(X, L, test_size=0.2, random_state=42)

    # Training Loop
    def train(model, loader, is_hyper=False):
        opt = optim.Adam(model.parameters(), lr=1e-3)
        # Loss: Pull samples from same class together, separate different classes
        # Simplified: Train to predict a "canonical" class embedding
        # For simplicity in PoC, we train to predict the Centroid
        centroids = {l: X[L == l].mean(axis=0) for l in unique_labels}

        for epoch in range(10):
            model.train()
            for batch_x, batch_l in loader:
                opt.zero_grad()
                y_pred = model(batch_x)

                # Target centroid for the class
                y_true_raw = np.array([centroids[l] for l in batch_l]).astype(np.float32)
                y_true = torch.from_numpy(y_true_raw)

                if is_hyper:
                    y_true_h = ExponentialMap()(y_true[:, :31])
                    loss = lorentz_dist(y_pred, y_true_h).mean()
                else:
                    # Euclidean target (128-d for comparison)
                    if y_pred.shape[1] == 128:
                        y_true = torch.cat([y_true, torch.zeros(y_true.shape[0], 96)], dim=1)
                    loss = nn.MSELoss()(y_pred, y_true)

                loss.backward()
                opt.step()

    # DataLoaders
    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, x, l): self.x, self.l = x, l
        def __len__(self): return len(self.x)
        def __getitem__(self, i): return self.x[i], self.l[i]

    loader_train = DataLoader(SimpleDataset(X_train, L_train), batch_size=128, shuffle=True)

    # Models
    print("[ARKHE] Treinando Euclidiano 128-d...")
    m_euc = EuclideanModel(32, 128)
    train(m_euc, loader_train, False)

    print("[ARKHE] Treinando Hiperbólico 32-d...")
    m_hyp = HyperbolicModel(32, 32)
    train(m_hyp, loader_train, True)

    # Evaluation
    def evaluate(model, is_hyper=False):
        model.eval()
        with torch.no_grad():
            latent = model(torch.from_numpy(X_test)).numpy()

        # Sample pairs
        indices = np.random.choice(len(X_test), 1000, replace=False)
        l_sampled = latent[indices]
        lab_sampled = L_test[indices]

        d_lat, d_tax = [], []
        for i in range(2000):
            a, b = np.random.choice(1000, 2, replace=False)
            if is_hyper:
                d = lorentz_dist(torch.from_numpy(l_sampled[a:a+1]), torch.from_numpy(l_sampled[b:b+1])).item()
            else:
                d = np.linalg.norm(l_sampled[a] - l_sampled[b])
            d_lat.append(d)
            d_tax.append(taxonomy_distances[(lab_sampled[a], lab_sampled[b])])

        return spearmanr(d_lat, d_tax)[0]

    corr_euc = evaluate(m_euc, False)
    corr_hyp = evaluate(m_hyp, True)

    print(f"Correlação Euclidiano (128-d): {corr_euc:.4f}")
    print(f"Correlação Hiperbólico (32-d): {corr_hyp:.4f}")

    with open("poc_metrics.json", "w") as f:
        json.dump({"euclidean_128d": corr_euc, "hyperbolic_32d": corr_hyp}, f)

    plt.figure(figsize=(8, 5))
    plt.bar(["Euclidiano (128-d)", "Hiperbólico (32-d)"], [corr_euc, corr_hyp], color=['#34495e', '#1abc9c'])
    plt.title("Preservação da Estrutura Hierárquica")
    plt.ylabel("Correlação de Spearman")
    plt.savefig("poc_comparison_viz.png")

if __name__ == "__main__":
    run_poc()
