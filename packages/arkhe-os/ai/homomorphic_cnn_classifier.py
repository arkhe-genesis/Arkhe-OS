import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional
import hashlib
import time

from arkhe_os.ai.coherence_cnn_classifier import CoherenceCNNClassifier, ClassificationResult, CoherenceState
from arkhe_os.crypto.hypergraph_fhe import HypergraphFHE

class SpatialAttention(nn.Module):
    def __init__(self, kernel_size=7):
        super().__init__()
        assert kernel_size in (3, 7), 'kernel size must be 3 or 7'
        padding = 3 if kernel_size == 7 else 1
        self.conv1 = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x_cat = torch.cat([avg_out, max_out], dim=1)
        out = self.conv1(x_cat)
        return x * self.sigmoid(out)

class DeepCoherenceCNNClassifier(CoherenceCNNClassifier):
    """
    A deeper version of CoherenceCNNClassifier adding more residual blocks
    and a Spatial Attention mechanism.
    """
    def __init__(self, input_channels=3, num_classes=6, embedding_dim=128, pretrained=False):
        super().__init__(input_channels, num_classes, embedding_dim, pretrained)

        # Deepen the network
        self.layer4 = self._make_layer(256, 512, blocks=2, stride=2)

        # Add spatial attention after the last block
        self.attention = SpatialAttention()

        # Update heads to use the new output dimension (512)
        self.fc_class = nn.Linear(512, num_classes)
        self.fc_embedding = nn.Linear(512, embedding_dim)
        self.fc_spatial = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 8)
        )
        self._initialize_weights()

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.attention(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)

        class_logits = self.fc_class(x)
        embedding = self.fc_embedding(x)
        spatial_metrics = self.fc_spatial(x)
        return class_logits, embedding, spatial_metrics


class HomomorphicCNNClassifier(nn.Module):
    """
    Wraps the DeepCoherenceCNNClassifier to process Homomorphically Encrypted (FHE) data.
    """
    def __init__(self, fhe_module: HypergraphFHE, base_classifier: Optional[DeepCoherenceCNNClassifier] = None):
        super().__init__()
        self.fhe = fhe_module
        self.classifier = base_classifier or DeepCoherenceCNNClassifier()

    def encrypt_input(self, image: torch.Tensor) -> torch.Tensor:
        """Encrypts the input image using the FHE module."""
        return self.fhe.encrypt(image)

    def classify_encrypted(self, encrypted_image: torch.Tensor, temperature: float = 1.0, return_probs: bool = True) -> ClassificationResult:
        """
        Classifies an already encrypted image.
        In a real FHE scenario, the classifier's operations would be homomorphic.
        For this simulation, we decrypt inside the secure enclave before passing
        it to the deep CNN, simulating the end-result of a homomorphic evaluation.
        """
        # Secure enclave decryption (simulated FHE evaluation)
        decrypted_image = self.fhe.decrypt(encrypted_image)

        # Pass through the deepened classifier
        return self.classifier.classify(decrypted_image, temperature=temperature, return_probs=return_probs)

    def classify(self, image: torch.Tensor, temperature: float = 1.0, return_probs: bool = True) -> ClassificationResult:
        """
        Standard interface: Encrypts the input, evaluates it 'homomorphically', and returns the result.
        """
        encrypted = self.encrypt_input(image)
        return self.classify_encrypted(encrypted, temperature, return_probs)
