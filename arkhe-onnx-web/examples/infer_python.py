import onnxruntime as ort
import numpy as np

def run_inference():
    # Load model
    session = ort.InferenceSession("../models/crystal_sae.onnx")

    # Create dummy data
    phases = np.random.randn(1, 768).astype(np.float32)

    # Run inference
    outputs = session.run(None, {"phases": phases})
    reconstructed, latent = outputs

    print(f"Reconstructed shape: {reconstructed.shape}")
    print(f"Latent shape: {latent.shape}")

if __name__ == "__main__":
    run_inference()
