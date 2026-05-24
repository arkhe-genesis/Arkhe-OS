import base64

code = """#!/usr/bin/env python3
# ARKHE OS Substrate 641 — Mechanistic Interpretability Layer
# Combined Modules 641.0 to 641.5
# Author: ORCID 0009-0005-2697-4668

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, List, Dict, Callable

def visualize_weights(model_path: str, layer_name: str = "embed", save_dir: str = "/tmp/arkhe/mechinterp"):
    \"\"\"Load ARKHE model weights and visualize first layer as heatmaps.\"\"\"

    model = torch.load(model_path, map_location="cpu")
    weights = model.get(layer_name, None)

    if weights is None:
        raise ValueError("Layer {0} not found in model".format(layer_name))

    weights = weights.detach().cpu().numpy()

    fig, axes = plt.subplots(8, 8, figsize=(16, 16))
    fig.suptitle("ARKHE Weight Visualization — {0}".format(layer_name), fontsize=14)

    for i, ax in enumerate(axes.flat):
        if i < weights.shape[0]:
            w = weights[i]
            side = int(np.sqrt(w.shape[0]))
            if side * side == w.shape[0]:
                w = w.reshape(side, side)
            ax.imshow(w, cmap="RdBu_r", vmin=-1, vmax=1)
            ax.set_title("Token {0}".format(i), fontsize=8)
        ax.axis("off")

    Path(save_dir).mkdir(parents=True, exist_ok=True)
    save_path = Path(save_dir) / "weights_{0}.png".format(layer_name)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    return str(save_path)

def detect_superposition(activations: torch.Tensor, threshold: float = 0.7) -> Tuple[float, List[int]]:
    n_samples, n_neurons = activations.shape
    norms = torch.norm(activations, dim=0, keepdim=True)
    normalized = activations / (norms + 1e-8)
    similarity = torch.mm(normalized.t(), normalized)

    polysemantic_neurons = []
    for i in range(n_neurons):
        similar_count = (similarity[i] > threshold).sum().item() - 1
        if similar_count > n_neurons * 0.1:
            polysemantic_neurons.append(i)

    score = len(polysemantic_neurons) / n_neurons
    return score, polysemantic_neurons

def compute_feature_dimensionality(activations: torch.Tensor) -> float:
    cov = torch.cov(activations.t())
    eigenvalues = torch.linalg.eigvalsh(cov)
    eigenvalues = eigenvalues[eigenvalues > 1e-10]

    pr = eigenvalues.sum().item() ** 2 / (eigenvalues ** 2).sum().item()
    return pr / activations.shape[1]

def fourier_analysis(weights: torch.Tensor, p: int = 113) -> Dict[str, torch.Tensor]:
    if weights.dim() == 2 and weights.shape[0] == p:
        fft = torch.fft.rfft(weights, dim=0, norm="ortho")
        power = torch.abs(fft) ** 2
        power_per_freq = power.sum(dim=1)

        return {
            "fourier_power": power_per_freq,
            "dominant_freqs": torch.topk(power_per_freq, k=5).indices,
            "entropy": -torch.sum(power_per_freq * torch.log(power_per_freq + 1e-10))
        }
    else:
        return {"error": "Unsupported weight shape for Fourier analysis"}

def track_grokking(checkpoints: List[str], p: int = 113) -> Dict[str, List]:
    history = {
        "steps": [],
        "dominant_freqs": [],
        "entropy": [],
        "accuracy": []
    }

    for i, ckpt_path in enumerate(checkpoints):
        ckpt = torch.load(ckpt_path, map_location="cpu")
        embed = ckpt["model"]["embed"]

        analysis = fourier_analysis(embed, p)
        history["steps"].append(i)
        history["dominant_freqs"].append(analysis["dominant_freqs"].tolist())
        history["entropy"].append(analysis["entropy"].item())
        history["accuracy"].append(ckpt.get("accuracy", 0.0))

    return history

def plot_grokking_trajectory(history: Dict[str, List], save_path: str = "/tmp/arkhe/grokking.png"):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(history["steps"], history["accuracy"], "b-", label="Accuracy")
    ax1.set_ylabel("Accuracy")
    ax1.legend()
    ax1.set_title("Grokking Trajectory — Tokenic Principle (624)")

    ax2.plot(history["steps"], history["entropy"], "r-", label="Fourier Entropy")
    ax2.set_xlabel("Training Step")
    ax2.set_ylabel("Fourier Entropy")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

    return save_path

def compute_induction_score(attention_pattern: torch.Tensor, token_ids: torch.Tensor) -> float:
    seq_len = attention_pattern.shape[0]
    score = 0.0
    count = 0

    for i in range(1, seq_len):
        prev_token = token_ids[i - 1]
        matches = (token_ids[:i-1] == prev_token).nonzero(as_tuple=True)[0]

        if len(matches) > 0:
            for match_pos in matches:
                next_pos = match_pos + 1
                if next_pos < i:
                    score += attention_pattern[i, next_pos].item()
                    count += 1

    return score / max(count, 1)

def map_attention_circuits(
    model,
    input_ids: torch.Tensor,
    n_layers: int,
    n_heads: int
) -> Dict[Tuple[int, int], float]:
    attention_patterns = []

    def hook_fn(module, input, output):
        attention_patterns.append(output.detach())

    hooks = []
    for layer in model.transformer.h:
        hooks.append(layer.attn.register_forward_hook(hook_fn))

    with torch.no_grad():
        _ = model(input_ids)

    for h in hooks:
        h.remove()

    circuit_scores = {}
    for layer_idx in range(n_layers):
        for head_idx in range(n_heads):
            attn = attention_patterns[layer_idx][0, head_idx]
            score = compute_induction_score(attn, input_ids[0])
            circuit_scores[(layer_idx, head_idx)] = score

    return circuit_scores

def find_induction_heads(circuit_scores: Dict[Tuple[int, int], float], threshold: float = 0.5) -> List[Tuple[int, int]]:
    return [(l, h) for (l, h), score in circuit_scores.items() if score > threshold]

def activation_patch(
    model,
    clean_input: torch.Tensor,
    corrupted_input: torch.Tensor,
    patch_layer: int,
    patch_neuron: int,
    patch_value: float = 0.0
) -> float:
    original_forwards = {}

    def make_hook(layer_idx, neuron_idx, value):
        def hook_fn(module, input, output):
            if layer_idx == patch_layer:
                output = output.clone()
                output[0, :, neuron_idx] = value
            return output
        return hook_fn

    target_module = model.transformer.h[patch_layer].mlp.c_proj
    hook = target_module.register_forward_hook(make_hook(patch_layer, patch_neuron, patch_value))

    with torch.no_grad():
        corrupted_output = model(corrupted_input).logits

    hook.remove()

    with torch.no_grad():
        clean_output = model(clean_input).logits

    kl = torch.nn.functional.kl_div(
        torch.nn.functional.log_softmax(corrupted_output, dim=-1),
        torch.nn.functional.softmax(clean_output, dim=-1),
        reduction="batchmean"
    )

    return kl.item()

def circuit_verification_suite(
    model,
    clean_input: torch.Tensor,
    corrupted_input: torch.Tensor,
    circuit_neurons: List[Tuple[int, int]]
) -> Dict[Tuple[int, int], float]:
    results = {}

    for layer, neuron in circuit_neurons:
        kl = activation_patch(model, clean_input, corrupted_input, layer, neuron)
        results[(layer, neuron)] = kl
        print("[641.4] Patch ({0}, {1}): KL = {2:.4f}".format(layer, neuron, kl))

    return results

class SparseAutoencoder(nn.Module):
    def __init__(self, input_dim: int, dict_size: int, sparsity_penalty: float = 1e-3):
        super().__init__()
        self.input_dim = input_dim
        self.dict_size = dict_size
        self.sparsity_penalty = sparsity_penalty

        self.encoder = nn.Linear(input_dim, dict_size, bias=True)
        self.decoder = nn.Linear(dict_size, input_dim, bias=False)

        nn.init.orthogonal_(self.decoder.weight)

        with torch.no_grad():
            self.encoder.weight.copy_(self.decoder.weight.t())

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = torch.relu(self.encoder(x))
        reconstruction = self.decoder(features)
        return reconstruction, features

    def loss(self, x: torch.Tensor) -> torch.Tensor:
        recon, features = self.forward(x)
        recon_loss = torch.mean((recon - x) ** 2)
        sparsity_loss = self.sparsity_penalty * torch.mean(torch.abs(features))
        return recon_loss + sparsity_loss

    def get_top_features(self, x: torch.Tensor, k: int = 5) -> Tuple[torch.Tensor, torch.Tensor]:
        _, features = self.forward(x)
        topk = torch.topk(features, k, dim=-1)
        return topk.indices, topk.values

    def interpret_feature(self, feature_idx: int, tokenizer=None, texts: List[str] = None):
        feature_vector = self.decoder.weight[feature_idx].detach().cpu().numpy()
        return {
            "feature_idx": feature_idx,
            "vector_norm": float(np.linalg.norm(feature_vector)),
            "top_dimensions": np.argsort(np.abs(feature_vector))[-10:].tolist()
        }

def train_sae(
    activations: torch.Tensor,
    dict_size: int = 8192,
    epochs: int = 1000,
    lr: float = 1e-3,
    batch_size: int = 256
) -> SparseAutoencoder:
    input_dim = activations.shape[1]
    sae = SparseAutoencoder(input_dim, dict_size)
    optimizer = torch.optim.Adam(sae.parameters(), lr=lr)

    dataset = torch.utils.data.TensorDataset(activations)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for epoch in range(epochs):
        total_loss = 0.0
        for (batch,) in loader:
            optimizer.zero_grad()
            loss = sae.loss(batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if epoch % 100 == 0:
            print("[641.5] Epoch {0}: Loss = {1:.6f}".format(epoch, total_loss / len(loader)))

    return sae

if __name__ == "__main__":
    pass
"""

b64 = base64.b64encode(code.encode('utf-8')).decode('utf-8')
print(b64)
