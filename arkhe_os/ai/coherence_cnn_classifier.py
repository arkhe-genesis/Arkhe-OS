import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass
import time
import hashlib

class CoherenceState(Enum):
    COHERENT = auto()
    DECOHERENT = auto()
    TRANSIENT = auto()
    INSTABLE = auto()
    SKYRMION_RICH = auto()
    UNKNOWN = auto()

@dataclass
class ClassificationResult:
    state: CoherenceState
    confidence: float
    state_probabilities: Dict[CoherenceState, float]
    spatial_features: Dict[str, float]
    timestamp: float
    frame_hash: str

class CoherenceCNNClassifier(nn.Module):
    def __init__(self, input_channels=3, num_classes=6, embedding_dim=128, pretrained=False):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(64, 64, blocks=2)
        self.layer2 = self._make_layer(64, 128, blocks=2, stride=2)
        self.layer3 = self._make_layer(128, 256, blocks=2, stride=2)

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc_class = nn.Linear(256, num_classes)
        self.fc_embedding = nn.Linear(256, embedding_dim)
        self.fc_spatial = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 8)
        )
        self.embedding_dim = embedding_dim
        self._initialize_weights()

    def _make_layer(self, in_channels, out_channels, blocks, stride=1):
        layers = []
        if stride != 1 or in_channels != out_channels:
            layers.append(nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False))
            layers.append(nn.BatchNorm2d(out_channels))
            layers.append(nn.ReLU(inplace=True))
        for _ in range(blocks):
            layers.append(nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False))
            layers.append(nn.BatchNorm2d(out_channels))
            layers.append(nn.ReLU(inplace=True))
            layers.append(nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False))
            layers.append(nn.BatchNorm2d(out_channels))
            layers.append(nn.ReLU(inplace=True))
        return nn.Sequential(*layers)

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.zeros_(m.bias)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        class_logits = self.fc_class(x)
        embedding = self.fc_embedding(x)
        spatial_metrics = self.fc_spatial(x)
        return class_logits, embedding, spatial_metrics

    def classify(self, image, temperature=1.0, return_probs=True):
        self.eval()
        if image.dim() == 3:
            image = image.permute(2, 0, 1).unsqueeze(0)
        if image.shape[-2:] != (256, 256):
            image = F.interpolate(image, size=(256, 256), mode='bilinear', align_corners=False)
        image = image * 2.0 - 1.0
        with torch.no_grad():
            logits, embedding, spatial_raw = self.forward(image)
            probs = F.softmax(logits / temperature, dim=1).squeeze(0)
            pred_idx = torch.argmax(probs).item()
            state = CoherenceState(pred_idx + 1)  # Fix 0-based index to 1-based enum
            confidence = probs[pred_idx].item()
            state_probs = {}
            if return_probs:
                for i, s in enumerate(CoherenceState):
                    state_probs[s] = probs[i].item()
            spatial_metrics = self._decode_spatial_metrics(spatial_raw.squeeze(0))
            frame_hash = hashlib.sha256(image.cpu().numpy().tobytes()).hexdigest()[:12]
            return ClassificationResult(
                state=state, confidence=confidence, state_probabilities=state_probs,
                spatial_features=spatial_metrics, timestamp=time.time(), frame_hash=frame_hash
            )

    def _decode_spatial_metrics(self, raw):
        return {
            'vorticity': torch.sigmoid(raw[0]).item(),
            'symmetry': torch.sigmoid(raw[1]).item(),
            'fragmentation': torch.sigmoid(raw[2]).item(),
            'contrast': torch.sigmoid(raw[3]).item(),
            'radial_coherence': torch.sigmoid(raw[4]).item(),
            'angular_variation': torch.sigmoid(raw[5]).item(),
            'spatial_frequency': torch.sigmoid(raw[6]).item(),
            'edge_density': torch.sigmoid(raw[7]).item()
        }

    def train_step(self, images, labels, optimizer, loss_weights=None):
        self.train()
        optimizer.zero_grad()
        logits, embedding, spatial_raw = self.forward(images)
        weights = loss_weights.get('class', 1.0) if loss_weights else 1.0
        class_loss = F.cross_entropy(logits, labels) * weights
        if loss_weights and 'embedding' in loss_weights:
            embed_loss = torch.mean(embedding ** 2) * loss_weights['embedding']
            class_loss += embed_loss
        class_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
        optimizer.step()
        preds = torch.argmax(logits, dim=1)
        accuracy = (preds == labels).float().mean().item()
        return {'loss': class_loss.item(), 'accuracy': accuracy, 'lr': optimizer.param_groups[0]['lr']}
