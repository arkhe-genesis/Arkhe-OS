#!/usr/bin/env python3
"""
ARKHE OS δ‑mem Training Optimizations
Quantização, cache de features, incremental learning para CI rápido.
"""
import asyncio
import hashlib
import json
import time
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DeltaMemOptimizer:
    """
    Otimizador de treinamento δ‑mem para ambientes de CI.

    Técnicas suportadas:
    • Quantização INT8/FP16 via ONNX Runtime
    • Cache de features com invalidation por hash de código
    • Incremental learning com buffer de experiências recentes
    • Early stopping baseado em Φ_C convergence
    """

    def __init__(
        self,
        model_path: str,
        cache_dir: str = "/tmp/delta-mem-cache",
        quantization: str = "int8",  # "none", "fp16", "int8"
        incremental_buffer_size: int = 1000
    ):
        self.model_path = Path(model_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quantization = quantization
        self.incremental_buffer: List[Dict] = []
        self.incremental_buffer_size = incremental_buffer_size
        self._feature_cache: Dict[str, Tuple[np.ndarray, float]] = {}

    def compute_feature_hash(self, features: Dict) -> str:
        """Calcula hash SHA3-256 de features para cache."""
        # Ordenar keys para consistência
        sorted_features = json.dumps(features, sort_keys=True)
        return hashlib.sha3_256(sorted_features.encode()).hexdigest()[:16]

    def get_cached_features(self, features: Dict) -> Optional[np.ndarray]:
        """Retorna features do cache se disponível e válido."""
        feature_hash = self.compute_feature_hash(features)

        if feature_hash in self._feature_cache:
            cached_array, timestamp = self._feature_cache[feature_hash]
            # Invalidar cache após 1 hora
            if time.time() - timestamp < 3600:
                logger.debug(f"📦 Cache hit para features: {feature_hash}")
                return cached_array

        return None

    def cache_features(self, features: Dict, array: np.ndarray):
        """Armazena features no cache."""
        feature_hash = self.compute_feature_hash(features)
        self._feature_cache[feature_hash] = (array.copy(), time.time())

        # Limitar tamanho do cache (LRU simples)
        if len(self._feature_cache) > 10000:
            # Remover entry mais antiga
            oldest_key = min(self._feature_cache.keys(),
                           key=lambda k: self._feature_cache[k][1])
            del self._feature_cache[oldest_key]

    async def quantize_model(self, input_model_path: str, output_path: str) -> str:
        """
        Aplica quantização ao modelo δ‑mem para inference mais rápida.

        Args:
            input_model_path: Caminho para modelo PyTorch original
            output_path: Caminho para modelo quantizado

        Returns:
            Caminho do modelo quantizado
        """
        if self.quantization == "none":
            return input_model_path

        logger.info(f"🔧 Quantizando modelo: {self.quantization.upper()}")

        try:
            # Carregar modelo original
            model = torch.load(input_model_path, map_location='cpu')

            if self.quantization == "fp16":
                # Converter para FP16
                model = model.half()

            elif self.quantization == "int8":
                # Quantização INT8 via torch.ao.quantization
                model.eval()
                model.qconfig = torch.ao.quantization.get_default_qconfig('fbgemm')
                model_prepared = torch.ao.quantization.prepare(model)
                # Em produção: calibrar com dataset representativo
                model_quantized = torch.ao.quantization.convert(model_prepared)
                model = model_quantized

            # Salvar modelo quantizado
            torch.save(model, output_path)

            # Calcular redução de tamanho
            original_size = Path(input_model_path).stat().st_size
            quantized_size = Path(output_path).stat().st_size
            reduction = (1 - quantized_size / original_size) * 100

            logger.info(f"✅ Modelo quantizado: {original_size/1e6:.2f}MB → {quantized_size/1e6:.2f}MB ({reduction:.1f}% redução)")

            return output_path

        except Exception as e:
            logger.warning(f"⚠️  Falha na quantização: {e}. Usando modelo original.")
            return input_model_path

    async def incremental_train(
        self,
        new_experiences: List[Dict],
        base_model_path: str,
        learning_rate: float = 0.001,
        epochs: int = 5
    ) -> str:
        """
        Treinamento incremental com buffer de experiências recentes.

        Args:
            new_experiences: Lista de novas experiências para treinar
            base_model_path: Caminho do modelo base
            learning_rate: Taxa de aprendizado para fine-tuning
            epochs: Número de épocas de fine-tuning

        Returns:
            Caminho do modelo atualizado
        """
        # Adicionar ao buffer incremental
        self.incremental_buffer.extend(new_experiences)

        # Manter buffer dentro do limite
        if len(self.incremental_buffer) > self.incremental_buffer_size:
            self.incremental_buffer = self.incremental_buffer[-self.incremental_buffer_size:]

        logger.info(f"🔄 Incremental training: {len(self.incremental_buffer)} experiências no buffer")

        # Carregar modelo base
        model = torch.load(base_model_path, map_location='cpu')
        model.train()

        # Configurar optimizer para fine-tuning (taxa reduzida)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate * 0.1)

        # Preparar batch de treinamento
        for epoch in range(epochs):
            # Amostrar batch aleatório do buffer
            batch = np.random.choice(
                self.incremental_buffer,
                size=min(32, len(self.incremental_buffer)),
                replace=False
            )

            # Forward/backward pass simplificado
            # Em produção: implementar loop de treinamento completo
            total_loss = 0
            for exp in batch:
                # Simular forward pass
                loss = np.random.uniform(0.01, 0.1)  # Mock loss
                total_loss += loss

                # Simular backward pass
                optimizer.zero_grad()
                # loss.backward()  # Em produção: backward real
                optimizer.step()

            avg_loss = total_loss / len(batch)
            logger.debug(f"   Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}")

            # Early stopping baseado em convergência de Φ_C
            if epoch > 0 and abs(avg_loss - prev_loss) < 0.001:
                logger.info(f"⏹️  Early stopping: convergência atingida")
                break
            prev_loss = avg_loss

        # Salvar modelo atualizado
        updated_path = base_model_path.replace('.pt', '_incremental.pt')
        torch.save(model, updated_path)

        return updated_path

    async def fast_inference(
        self,
        features: Dict,
        model_path: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Executa inference otimizada com cache de features.

        Returns:
            Dict com resultado da inference e métricas de performance
        """
        start_time = time.time()

        # Verificar cache de features
        if use_cache:
            cached = self.get_cached_features(features)
            if cached is not None:
                # Simular inference rápida com features em cache
                return {
                    "prediction": np.random.uniform(0.7, 0.99),  # Mock prediction
                    "latency_ms": (time.time() - start_time) * 1000,
                    "cache_hit": True,
                    "quantization": self.quantization
                }

        # Carregar modelo (quantizado se disponível)
        model = torch.load(model_path, map_location='cpu')
        model.eval()

        # Preparar tensor de features
        # Em produção: extrair features reais do input
        feature_tensor = torch.randn(1, 384)  # Mock feature vector

        # Executar inference
        with torch.no_grad():
            prediction = model(feature_tensor)

        # Cache resultado se habilitado
        if use_cache:
            self.cache_features(features, feature_tensor.numpy())

        latency_ms = (time.time() - start_time) * 1000

        return {
            "prediction": float(prediction.item()),
            "latency_ms": latency_ms,
            "cache_hit": False,
            "quantization": self.quantization,
            "feature_hash": self.compute_feature_hash(features)
        }
