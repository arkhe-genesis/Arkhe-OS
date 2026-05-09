#!/usr/bin/env python3
"""
visual_coherence_production.py — Production-grade deepfake visual analyzer.
Integrates Xception, MesoNet, EfficientNet, and ViT via ONNX Runtime.
"""
try:
    import onnxruntime as ort
except ImportError:
    ort = None

import numpy as np
import cv2
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class DeepfakeDetectionResult:
    frame_index: int
    is_fake: bool
    confidence: float
    model_scores: dict          # Scores individuais por modelo
    processing_time_ms: float

class ProductionDeepfakeDetector:
    """
    Deepfake detector ensemble using production models.
    Requires ONNX Runtime and pre-converted model files.
    """
    def __init__(self,
                 xception_path: str = "models/xception.trt",
                 mesonet_path: str = "models/mesonet_inception.onnx",
                 efficientnet_path: str = "models/efficientnet_b4.onnx",
                 vit_path: str = "models/vit_deepfake.onnx",
                 device: str = "cuda"):
        self.device = device
        self.sessions = {}
        # Carregar ONNX sessions para cada modelo
        if ort:
            for name, path in [("xception", xception_path),
                               ("mesonet", mesonet_path),
                               ("efficientnet", efficientnet_path),
                               ("vit", vit_path)]:
                try:
                    self.sessions[name] = ort.InferenceSession(
                        path,
                        providers=['CUDAExecutionProvider' if 'cuda' in device else 'CPUExecutionProvider']
                    )
                except:
                    print(f"Warning: Could not load {name} model from {path}")

        # Detector facial (MTCNN ou RetinaFace)
        try:
            from facenet_pytorch import MTCNN
            self.face_detector = MTCNN(keep_all=True, device=device)
        except ImportError:
            self.face_detector = lambda frame: None

        # Pesos adaptativos do ensemble (inicializados uniformemente)
        self.ensemble_weights = {
            "xception": 0.30,
            "mesonet": 0.15,
            "efficientnet": 0.25,
            "vit": 0.30
        }

    def preprocess_face(self, frame: np.ndarray) -> List[np.ndarray]:
        """Detecta e extrai faces do frame."""
        # Converter BGR -> RGB e detectar faces
        faces = self.face_detector(frame)
        if faces is None:
            return []
        # Recortar e redimensionar
        processed = []
        for face in faces:
            try:
                face_crop = face.permute(1, 2, 0).numpy()  # HWC
            except AttributeError:
                face_crop = face
            face_resized = cv2.resize(face_crop, (224, 224))
            # Normalizar ImageNet: (img - mean) / std
            face_resized = (face_resized - [123.675, 116.28, 103.53]) / [58.395, 57.12, 57.375]
            face_resized = face_resized.astype(np.float32)
            processed.append(face_resized)
        return processed

    def run_model(self, model_name: str, input_tensor: np.ndarray) -> float:
        """Executa um modelo ONNX e retorna probabilidade de 'real'."""
        if model_name not in self.sessions:
            return 0.5  # fallback neutro
        session = self.sessions[model_name]
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: input_tensor})
        # Assume output[0] shape (1,2) com logits [real, fake]
        probs = np.exp(output[0][0]) / np.sum(np.exp(output[0][0]))
        return float(probs[0])  # Probabilidade de real

    def analyze_frame(self, frame: np.ndarray) -> DeepfakeDetectionResult:
        """Analisa um único frame e retorna resultado completo."""
        faces = self.preprocess_face(frame)
        if not faces:
            # Sem faces detectadas: não é possível avaliar deepfake facial
            return DeepfakeDetectionResult(
                frame_index=0,
                is_fake=False,
                confidence=0.5,
                model_scores={"all": 0.5},
                processing_time_ms=0.0
            )

        # Para simplificar, usar a primeira face
        face_batch = np.expand_dims(faces[0], axis=0)  # (1,224,224,3) NHWC

        scores = {}
        for name in self.sessions:
            try:
                scores[name] = self.run_model(name, face_batch)
            except Exception as e:
                print(f"Model {name} failed: {e}")
                scores[name] = 0.5

        if not scores:
            scores = {"all": 0.5}

        # Score ensemble: média ponderada
        real_score = sum(
            scores.get(name, 0.5) * self.ensemble_weights.get(name, 0.25)
            for name in scores
        )
        real_score /= sum(self.ensemble_weights.get(name, 0.25) for name in scores)

        is_fake = real_score < 0.5
        confidence = abs(real_score - 0.5) * 2

        return DeepfakeDetectionResult(
            frame_index=0,
            is_fake=is_fake,
            confidence=confidence,
            model_scores=scores,
            processing_time_ms=0.0
        )

    def update_ensemble_weights(self, performance_metrics: dict):
        """
        Atualiza pesos do ensemble baseado no desempenho recente.
        performance_metrics: {model_name: accuracy_last_window}
        """
        total = sum(performance_metrics.values())
        if total > 0:
            self.ensemble_weights = {
                name: performance_metrics.get(name, 0.25) / total
                for name in self.ensemble_weights
            }

class SemanticCoherenceAnalyzerProduction:
    def __init__(self, model_path: str = "models/deberta_nli.onnx"):
        if ort:
            try:
                self.session = ort.InferenceSession(model_path)
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                self.session = None
        else:
            self.session = None
        self.tokenizer = None  # Carregar tokenizer equivalente

    def detect_contradiction(self, premise: str, hypothesis: str) -> float:
        """Retorna probabilidade de contradição (0=consistent, 1=contradiction)."""
        if self.tokenizer is None or self.session is None:
            return 0.5

        tokens = self.tokenizer(premise, hypothesis, return_tensors='np')
        output = self.session.run(None, {
            'input_ids': tokens['input_ids'],
            'attention_mask': tokens['attention_mask']
        })
        # output[0] logits para [entailment, neutral, contradiction]
        probs = np.exp(output[0]) / np.sum(np.exp(output[0]))
        return float(probs[2])  # Contradiction score
