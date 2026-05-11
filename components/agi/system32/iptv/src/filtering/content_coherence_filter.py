#!/usr/bin/env python3
"""
content_coherence_filter.py — Filtro de coerência para detecção de deepfakes/manipulação.
Analisa streams de vídeo em tempo real usando métricas de coerência visual, auditiva e semântica.
"""
import asyncio
import time
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import cv2
from transformers import AutoModel, AutoTokenizer

class ManipulationType(Enum):
    DEEPFAKE = "deepfake"
    AUDIO_TAMPERING = "audio_tampering"
    CONTEXTUAL_MANIPULATION = "contextual_manipulation"
    METADATA_SPOOFING = "metadata_spoofing"
    UNKNOWN = "unknown"

@dataclass
class CoherenceAnalysis:
    """Resultado da análise de coerência de conteúdo."""
    stream_id: str
    timestamp: float
    visual_coherence: float      # Φ_visual ∈ [0, 1]
    audio_coherence: float       # Φ_audio ∈ [0, 1]
    semantic_coherence: float    # Φ_semantic ∈ [0, 1]
    anomaly_score: float         # Φ_anomaly ∈ [0, 1] (maior = mais suspeito)
    overall_phi_c: float         # Φ_C combinado
    manipulation_detected: bool
    manipulation_type: Optional[ManipulationType]
    confidence: float
    frame_samples_analyzed: int

class VisualCoherenceAnalyzer:
    """Analisa coerência visual para detectar deepfakes e manipulações."""

    def __init__(self, model_path: Optional[str] = None):
        # Carregar modelo pré-treinado para detecção de deepfakes
        # Em produção: usar Xception, MesoNet, ou modelo customizado
        self.model = self._load_deepfake_detector(model_path)
        self.frame_buffer: List[np.ndarray] = []
        self.buffer_size = 16  # Analisar janelas de 16 frames

    def _load_deepfake_detector(self, model_path: Optional[str]) -> nn.Module:
        """Carrega modelo de detecção de deepfakes."""
        # Placeholder: em produção, carregar modelo real
        class SimpleDeepfakeDetector(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = nn.Conv2d(3, 64, kernel_size=3, padding=1)
                self.pool = nn.AdaptiveAvgPool2d(1)
                self.classifier = nn.Linear(64, 2)  # real vs fake

            def forward(self, x):
                x = torch.relu(self.conv(x))
                x = self.pool(x).flatten(1)
                return self.classifier(x)

        model = SimpleDeepfakeDetector()
        if model_path:
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.eval()
        return model

    def analyze_frame_batch(self, frames: List[np.ndarray]) -> float:
        """Analisa batch de frames e retorna score de coerência visual."""
        if not frames:
            return 0.5  # Neutro se sem dados

        # Pré-processar frames
        processed = []
        for frame in frames:
            # Redimensionar para input do modelo
            frame_resized = cv2.resize(frame, (224, 224))
            frame_norm = frame_resized.astype(np.float32) / 255.0
            frame_tensor = torch.from_numpy(frame_norm).permute(2, 0, 1).unsqueeze(0)
            processed.append(frame_tensor)

        if not processed:
            return 0.5

        # Empilhar batch e executar inferência
        batch = torch.cat(processed, dim=0)
        with torch.no_grad():
            logits = self.model(batch)
            probs = torch.softmax(logits, dim=1)
            # Probabilidade de ser "real" (coerente)
            real_probs = probs[:, 0].numpy()

        # Coerência visual = média das probabilidades de "real"
        return float(np.mean(real_probs))

    def detect_temporal_inconsistencies(self, frames: List[np.ndarray]) -> float:
        """Detecta inconsistências temporais entre frames (sinal de manipulação)."""
        if len(frames) < 2:
            return 0.0  # Sem inconsistências detectáveis

        inconsistencies = []
        for i in range(1, len(frames)):
            # Calcular diferença óptica entre frames consecutivos
            prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_RGB2GRAY)
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)

            # Fluxo óptico
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            # Magnitude do fluxo
            magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            avg_magnitude = np.mean(magnitude)

            # Inconsistência = desvio da magnitude esperada
            # (valores muito altos ou muito baixos podem indicar manipulação)
            expected_range = (0.5, 15.0)  # Faixa normal para vídeo natural
            if not (expected_range[0] <= avg_magnitude <= expected_range[1]):
                inconsistencies.append(abs(avg_magnitude - np.mean(expected_range)))

        return float(np.mean(inconsistencies)) if inconsistencies else 0.0

class AudioCoherenceAnalyzer:
    """Analisa coerência auditiva para detectar tampering de áudio."""

    def analyze_audio_segment(self, audio_samples: np.ndarray,
                             sample_rate: int) -> float:
        """Analisa segmento de áudio e retorna score de coerência."""
        # Placeholder: em produção, usar análise espectral, detecção de clones de voz, etc.

        # Métricas simples de coerência:
        # 1. Consistência de volume
        volume_std = np.std(np.abs(audio_samples))
        volume_coherence = 1.0 - min(1.0, volume_std / 0.5)  # Normalizar

        # 2. Consistência espectral (simplificado)
        # Em produção: usar FFT e comparar com padrões de voz natural
        spectral_coherence = 0.85  # Placeholder

        # 3. Detecção de artefatos de compressão/edição
        artifact_score = 0.1  # Placeholder: menor = menos artefatos

        # Coerência combinada
        return 0.4 * volume_coherence + 0.4 * spectral_coherence + 0.2 * (1 - artifact_score)

class SemanticCoherenceAnalyzer:
    """Analisa coerência semântica entre áudio, vídeo e contexto."""

    def __init__(self, nlp_model: str = "bert-base-multilingual-cased"):
        self.tokenizer = AutoTokenizer.from_pretrained(nlp_model)
        self.model = AutoModel.from_pretrained(nlp_model)

    def analyze_semantic_alignment(self,
                                  transcript: str,
                                  visual_context: str,
                                  metadata: Dict) -> float:
        """Analisa alinhamento semântico entre diferentes modalidades."""
        # Placeholder: em produção, usar modelos multimodais (CLIP, FLAVA, etc.)

        # Métricas de coerência semântica:
        # 1. Consistência entre transcrição e contexto visual
        transcript_context_score = self._compute_text_similarity(
            transcript, visual_context
        )

        # 2. Consistência com metadados declarados
        metadata_consistency = self._check_metadata_consistency(
            transcript, metadata
        )

        # 3. Detecção de contradições lógicas
        contradiction_score = self._detect_logical_contradictions(transcript)

        # Coerência semântica combinada
        return (
            0.5 * transcript_context_score +
            0.3 * metadata_consistency +
            0.2 * (1.0 - contradiction_score)
        )

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """Computa similaridade semântica entre dois textos."""
        # Placeholder: usar embeddings e cosine similarity
        return 0.85  # Placeholder

    def _check_metadata_consistency(self, text: str, metadata: Dict) -> float:
        """Verifica consistência entre conteúdo e metadados."""
        # Placeholder: verificar se título, descrição, tags correspondem ao conteúdo
        return 0.9  # Placeholder

    def _detect_logical_contradictions(self, text: str) -> float:
        """Detecta contradições lógicas no conteúdo."""
        # Placeholder: usar NLI (Natural Language Inference)
        return 0.05  # Placeholder: baixo = poucas contradições

class ContentCoherenceFilter:
    """Filtro principal de coerência para streams de vídeo."""

    def __init__(self,
                 visual_analyzer: Optional[VisualCoherenceAnalyzer] = None,
                 audio_analyzer: Optional[AudioCoherenceAnalyzer] = None,
                 semantic_analyzer: Optional[SemanticCoherenceAnalyzer] = None,
                 coherence_threshold: float = 0.7,
                 anomaly_threshold: float = 0.6):
        self.visual = visual_analyzer or VisualCoherenceAnalyzer()
        self.audio = audio_analyzer or AudioCoherenceAnalyzer()
        self.semantic = semantic_analyzer or SemanticCoherenceAnalyzer()

        self.coherence_threshold = coherence_threshold
        self.anomaly_threshold = anomaly_threshold

        # Pesos para combinação de métricas
        self.weights = {
            'visual': 0.35,
            'audio': 0.25,
            'semantic': 0.25,
            'anomaly': 0.15  # Penalidade
        }

        # Cache de análises recentes para otimização
        self.analysis_cache: Dict[str, CoherenceAnalysis] = {}

    async def analyze_stream_segment(self,
                                    stream_id: str,
                                    video_frames: List[np.ndarray],
                                    audio_samples: Optional[np.ndarray],
                                    transcript: Optional[str],
                                    visual_context: Optional[str],
                                    metadata: Dict) -> CoherenceAnalysis:
        """Analisa segmento de stream e retorna análise de coerência."""

        timestamp = time.time()

        # 1. Análise visual
        visual_coh = self.visual.analyze_frame_batch(video_frames)
        temporal_inconsistency = self.visual.detect_temporal_inconsistencies(video_frames)

        # 2. Análise auditiva (se áudio disponível)
        audio_coh = 0.85  # Default se sem áudio
        if audio_samples is not None and len(audio_samples) > 0:
            audio_coh = self.audio.analyze_audio_segment(audio_samples, 44100)

        # 3. Análise semântica (se transcrição disponível)
        semantic_coh = 0.85  # Default se sem transcrição
        if transcript and visual_context:
            semantic_coh = self.semantic.analyze_semantic_alignment(
                transcript, visual_context, metadata
            )

        # 4. Score de anomalia (quanto maior, mais suspeito)
        anomaly_score = (
            0.6 * temporal_inconsistency +  # Inconsistências visuais
            0.3 * (1.0 - audio_coh) +        # Problemas de áudio
            0.1 * (1.0 - semantic_coh)       # Problemas semânticos
        )

        # 5. Coerência geral combinada
        overall_phi_c = (
            self.weights['visual'] * visual_coh +
            self.weights['audio'] * audio_coh +
            self.weights['semantic'] * semantic_coh -
            self.weights['anomaly'] * anomaly_score
        )
        overall_phi_c = max(0.0, min(1.0, overall_phi_c))  # Clamp [0, 1]

        # 6. Decisão: manipulação detectada?
        manipulation_detected = (
            overall_phi_c < self.coherence_threshold or
            anomaly_score > self.anomaly_threshold
        )

        # 7. Classificar tipo de manipulação (se detectada)
        manipulation_type = None
        if manipulation_detected:
            if temporal_inconsistency > 0.5:
                manipulation_type = ManipulationType.DEEPFAKE
            elif audio_coh < 0.6:
                manipulation_type = ManipulationType.AUDIO_TAMPERING
            elif semantic_coh < 0.6:
                manipulation_type = ManipulationType.CONTEXTUAL_MANIPULATION
            else:
                manipulation_type = ManipulationType.UNKNOWN

        # 8. Calcular confiança da análise
        confidence = 0.7 + 0.3 * (len(video_frames) / self.visual.buffer_size)
        confidence = min(0.99, confidence)  # Máximo 99%

        # Criar resultado
        analysis = CoherenceAnalysis(
            stream_id=stream_id,
            timestamp=timestamp,
            visual_coherence=visual_coh,
            audio_coherence=audio_coh,
            semantic_coherence=semantic_coh,
            anomaly_score=anomaly_score,
            overall_phi_c=overall_phi_c,
            manipulation_detected=manipulation_detected,
            manipulation_type=manipulation_type,
            confidence=confidence,
            frame_samples_analyzed=len(video_frames)
        )

        # Cache para consultas rápidas
        self.analysis_cache[stream_id] = analysis

        return analysis

    def should_block_stream(self, analysis: CoherenceAnalysis) -> bool:
        """Decide se stream deve ser bloqueado baseado na análise."""
        # Bloquear se:
        # 1. Manipulação detectada com alta confiança
        # 2. Coerência muito baixa
        # 3. Anomalia muito alta

        if analysis.manipulation_detected and analysis.confidence > 0.85:
            return True
        if analysis.overall_phi_c < 0.5:
            return True
        if analysis.anomaly_score > 0.8:
            return True

        return False

    async def get_stream_health_report(self,
                                       stream_id: str,
                                       window_seconds: int = 60) -> Dict:
        """Gera relatório de saúde para um stream baseado em análises recentes."""
        # Placeholder: agregar análises dos últimos N segundos
        # Em produção: consultar banco de dados de análises

        recent = [
            a for a in self.analysis_cache.values()
            if a.stream_id == stream_id and
            time.time() - a.timestamp < window_seconds
        ]

        if not recent:
            return {"status": "no_data", "stream_id": stream_id}

        avg_phi_c = np.mean([a.overall_phi_c for a in recent])
        manipulation_count = sum(1 for a in recent if a.manipulation_detected)

        return {
            "stream_id": stream_id,
            "window_seconds": window_seconds,
            "analyses_count": len(recent),
            "avg_coherence": float(avg_phi_c),
            "min_coherence": float(min(a.overall_phi_c for a in recent)),
            "manipulation_detections": manipulation_count,
            "health_status": "healthy" if avg_phi_c > 0.75 else
                           "degraded" if avg_phi_c > 0.6 else "critical",
            "recommendation": "allow" if avg_phi_c > 0.7 and manipulation_count == 0 else
                            "review" if avg_phi_c > 0.5 else "block"
        }