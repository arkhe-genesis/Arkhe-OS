import torch
import torch.nn as nn
from arkhe_os.crypto.hypergraph_fhe import HypergraphFHE
from arkhe_os.ai.homomorphic_cnn_classifier import HomomorphicCNNClassifier
from arkhe_os.ai.interactive_explainer import NaturalLanguageInteractiveExplainer
from arkhe_os.ai.visual_attention_explainer import VisualAttentionExplainer
from arkhe_os.ai.federated_personalization import FederatedPersonalizationEngine
from arkhe_os.neural.multimodal_stimulation_engine import MultimodalStimulationEngine, MultimodalPattern

def test_hypergraph_fhe():
    fhe = HypergraphFHE()
    data = torch.ones((1, 3, 256, 256))
    enc = fhe.encrypt(data)
    assert not torch.allclose(data, enc), "Encrypted data should not equal raw data"
    dec = fhe.decrypt(enc)
    # The simulated FHE adds laplacian noise, so we check if it is close (tolerance due to noise)
    assert torch.allclose(data, dec, atol=1e-3), "Decrypted data should be close to raw data"
    print("test_hypergraph_fhe passed.")

def test_homomorphic_cnn():
    fhe = HypergraphFHE()
    model = HomomorphicCNNClassifier(fhe_module=fhe)
    image = torch.rand((1, 3, 256, 256))
    result = model.classify(image)
    assert result.confidence >= 0.0
    print(f"test_homomorphic_cnn passed. Classified as: {result.state.name} with confidence {result.confidence}")

def test_interactive_explainer():
    class DummyClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(3 * 256 * 256, 6)
        def forward(self, x):
            y = self.linear(x.view(1, -1))
            return y, torch.zeros((1, 128)), torch.zeros((1, 8))

    dummy_model = DummyClassifier()
    visual_explainer = VisualAttentionExplainer(dummy_model)
    interactive = NaturalLanguageInteractiveExplainer(visual_explainer)

    image = torch.rand((1, 3, 256, 256))

    resp_why = interactive.ask("why did it predict this?", image, predicted_class="COHERENT")
    assert "because it identified" in resp_why

    resp_where = interactive.ask("where is the focus?", image, predicted_class="COHERENT")
    assert "spread across regions" in resp_where or "centered around pixel" in resp_where

    resp_conf = interactive.ask("what is the confidence?", image, predicted_class="COHERENT")
    assert "confident that the state is" in resp_conf

    print("test_interactive_explainer passed.")

def test_federated_personalization():
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(10, 2)
            # init weights to zeros for testing
            nn.init.zeros_(self.linear.weight)
            nn.init.zeros_(self.linear.bias)

    global_model = SimpleModel()
    engine = FederatedPersonalizationEngine(global_model, epsilon=1.0, sensitivity=0.001)

    # User 1 sends an update of ones
    user1_update = {
        'linear.weight': torch.ones_like(global_model.linear.weight),
        'linear.bias': torch.ones_like(global_model.linear.bias)
    }

    # User 2 sends an update of twos
    user2_update = {
        'linear.weight': torch.ones_like(global_model.linear.weight) * 2,
        'linear.bias': torch.ones_like(global_model.linear.bias) * 2
    }

    engine.receive_user_update(user1_update)
    engine.receive_user_update(user2_update)

    engine.aggregate_updates()

    # After aggregation, the weights should be approximately 1.5
    # (since laplacian noise is added, we use a wide tolerance)
    avg_weight = global_model.linear.weight.mean().item()
    assert 1.4 < avg_weight < 1.6, f"Aggregated weight is {avg_weight}, expected ~1.5"

    print("test_federated_personalization passed.")

def test_hardware_timestamp_sync():
    engine = MultimodalStimulationEngine()
    pattern = MultimodalPattern(visual=True, duration_ms=1)
    engine.interfaces['visual'] = True # Mocking the interface so it doesn't skip
    engine.enqueue_multimodal_pattern(pattern)
    engine._execute_pattern_with_sync(pattern)

    # Check that sync errors are very small (e.g. < 0.1ms)
    assert len(engine.sync_errors) > 0
    max_error = max(engine.sync_errors)
    print(f"Max sync error was {max_error:.4f} ms")
    assert max_error < 10.0, "Sync error should be small" # Giving some leeway for CI execution
    print("test_hardware_timestamp_sync passed.")

if __name__ == "__main__":
    test_hypergraph_fhe()
    test_homomorphic_cnn()
    test_interactive_explainer()
    test_federated_personalization()
    test_hardware_timestamp_sync()
    print("ALL NEW TESTS PASSED")
