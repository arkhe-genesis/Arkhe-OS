import time
import numpy as np

def benchmark_probability_model(n_samples=10000, dimensions=2048):
    print(f"Benchmarking probability model with {n_samples} samples of dimension {dimensions}...")

    # Simulating style embedding vectors
    embeddings = np.random.randn(n_samples, dimensions).astype(np.float32)
    # Normalize to unit sphere (common in CLIP)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    target_style = np.random.randn(dimensions).astype(np.float32)
    target_style = target_style / np.linalg.norm(target_style)

    start = time.time()

    # Cosine similarity matrix multiplication
    similarities = np.dot(embeddings, target_style)

    # Softmax temperature scaling
    temperature = 0.05
    scaled_sims = similarities / temperature

    # Stable softmax
    max_sim = np.max(scaled_sims)
    exp_sims = np.exp(scaled_sims - max_sim)
    probabilities = exp_sims / np.sum(exp_sims)

    end = time.time()

    duration = end - start

    print(f"Executed similarity and probability distribution in {duration:.4f} seconds.")
    print(f"Max Probability assigned: {np.max(probabilities):.4f}")
    print(f"Min Probability assigned: {np.min(probabilities):.4e}")
    print(f"Sum of probabilities: {np.sum(probabilities):.4f}")

if __name__ == "__main__":
    benchmark_probability_model(50000, 2048)
