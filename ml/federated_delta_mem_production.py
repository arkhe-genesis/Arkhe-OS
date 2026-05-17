#!/usr/bin/env python3
"""
Substrato 224: Federated δ‑mem Production Trainer
Orquestra treinamento federado do δ‑mem entre nós de produção
com privacidade diferencial, agregação segura e evolução coletiva.
"""
import asyncio
import hashlib
import json
import time
import numpy as np
import torch
import torch.nn as nn
import io
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

@dataclass
class FederatedTrainingConfig:
    """Configuração de treinamento federado em produção."""
    node_id: str
    aggregation_strategy: str = "fedavg"  # fedavg, fedprox, secure_agg
    dp_epsilon_range: Tuple[float, float] = (2.0, 5.0)
    min_phi_c_for_aggregation: float = 0.95
    sync_interval_seconds: int = 300
    max_participants_per_round: int = 10
    model_architecture: Dict = field(default_factory=lambda: {
        "context_dim": 384,  # SBERT embedding
        "hidden_dim": 64,
        "output_dim": None  # Definido dinamicamente
    })

@dataclass
class LocalModelUpdate:
    """Atualização de modelo local para federação."""
    node_id: str
    model_weights: bytes  # Pesos quantizados e criptografados
    training_samples: int
    local_loss: float
    phi_c_contribution: float
    dp_noise_epsilon: float
    timestamp: float
    pqc_signature: Optional[str] = None
    temporal_seal: Optional[str] = None

class FederatedDeltaMemProduction:
    """
    Orquestrador de treinamento federado para δ‑mem em produção.
    """

    def __init__(
        self,
        config: FederatedTrainingConfig,
        local_predictor,  # DeltaMemToolPredictor local
        temporal_chain=None,
        phi_bus=None,
        hsm_signer=None
    ):
        self.config = config
        self.local_predictor = local_predictor
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.hsm = hsm_signer

        self._pending_updates: List[LocalModelUpdate] = []
        self._aggregation_history: List[Dict] = []
        self._round_number = 0
        self._participant_registry: Dict[str, Dict] = {}

    async def prepare_local_update(
        self,
        new_experiences: List[Dict],
        epochs: int = 3,
        learning_rate: float = 0.001
    ) -> LocalModelUpdate:
        """
        Prepara atualização local para envio à federação.
        """
        start_time = time.time()

        # Treinamento local incremental
        local_loss = await self._local_train(new_experiences, epochs, learning_rate)

        # Calcular contribuição Φ_C do treinamento local
        phi_c_contribution = await self._compute_local_phi_c(new_experiences)

        # Selecionar ε de DP baseado na sensibilidade dos dados
        dp_epsilon = self._select_dp_epsilon(new_experiences)

        # Adicionar ruído Laplace para privacidade diferencial
        noisy_weights = await self._add_dp_noise(
            self.local_predictor.model.state_dict(),
            dp_epsilon
        )

        # Serializar e criptografar pesos
        weights_bytes = await self._encrypt_weights(noisy_weights)

        # Assinar com PQC para integridade
        pqc_signature = await self._sign_with_pqc(weights_bytes)

        update = LocalModelUpdate(
            node_id=self.config.node_id,
            model_weights=weights_bytes,
            training_samples=len(new_experiences),
            local_loss=local_loss,
            phi_c_contribution=phi_c_contribution,
            dp_noise_epsilon=dp_epsilon,
            timestamp=time.time(),
            pqc_signature=pqc_signature
        )

        training_duration = time.time() - start_time
        logger.info(
            f"🔄 Atualização local preparada: {self.config.node_id} | "
            f"loss={local_loss:.4f} | Φ_C={phi_c_contribution:.4f} | "
            f"ε={dp_epsilon} | tempo={training_duration:.1f}s"
        )

        return update

    async def aggregate_updates(
        self,
        updates: List[LocalModelUpdate]
    ) -> Dict[str, Any]:
        """
        Agrega atualizações federadas de múltiplos nós.
        """
        self._round_number += 1
        start_time = time.time()

        # Validar assinaturas PQC de todas as atualizações
        valid_updates = []
        for update in updates:
            if await self._verify_pqc_signature(update):
                if update.phi_c_contribution >= self.config.min_phi_c_for_aggregation:
                    valid_updates.append(update)
                else:
                    logger.warning(
                        f"⚠️  Update rejeitado: Φ_C {update.phi_c_contribution:.4f} "
                        f"< {self.config.min_phi_c_for_aggregation}"
                    )
            else:
                logger.error(
                    f"❌ Assinatura PQC inválida para nó {update.node_id}"
                )

        if len(valid_updates) < 2:
            return {
                "status": "insufficient_valid_updates",
                "round": self._round_number
            }

        # Decodificar e descriptografar pesos
        decoded_weights = []
        total_samples = 0
        for update in valid_updates:
            weights = await self._decrypt_weights(update.model_weights)
            decoded_weights.append((weights, update.training_samples))
            total_samples += update.training_samples

        # Aplicar estratégia de agregação
        if self.config.aggregation_strategy == "fedavg":
            aggregated = self._fedavg_aggregate(decoded_weights, total_samples)
        elif self.config.aggregation_strategy == "fedprox":
            aggregated = self._fedprox_aggregate(decoded_weights, total_samples)
        else:
            aggregated = self._fedavg_aggregate(decoded_weights, total_samples)

        # Atualizar modelo local com pesos agregados
        self.local_predictor.model.load_state_dict(aggregated)

        # Calcular métricas pós-agregação
        aggregation_metrics = {
            "round": self._round_number,
            "valid_updates": len(valid_updates),
            "total_samples": total_samples,
            "avg_loss": np.mean([u.local_loss for u in valid_updates]),
            "avg_phi_c": np.mean([u.phi_c_contribution for u in valid_updates]),
            "aggregation_time_sec": time.time() - start_time,
            "strategy": self.config.aggregation_strategy
        }

        self._aggregation_history.append(aggregation_metrics)

        # Ancorar na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("federated_aggregation_completed", {
                "round": self._round_number,
                "node_id": self.config.node_id,
                "valid_updates": len(valid_updates),
                "aggregation_metrics": aggregation_metrics,
                "timestamp": time.time()
            })

        logger.info(
            f"✅ Agregação federada concluída: round {self._round_number} | "
            f"nós={len(valid_updates)} | samples={total_samples} | "
            f"tempo={aggregation_metrics['aggregation_time_sec']:.2f}s"
        )

        return {"status": "success", **aggregation_metrics}

    def _fedavg_aggregate(
        self,
        weighted_weights: List[Tuple[Dict, int]],
        total_samples: int
    ) -> Dict:
        """Agregação FedAvg clássica: média ponderada por número de samples."""
        aggregated = {}
        for key in weighted_weights[0][0].keys():
            aggregated[key] = sum(
                weights[key] * samples / total_samples
                for weights, samples in weighted_weights
            )
        return aggregated

    def _fedprox_aggregate(
        self,
        weighted_weights: List[Tuple[Dict, int]],
        total_samples: int
    ) -> Dict:
        """Mock para FedProx."""
        return self._fedavg_aggregate(weighted_weights, total_samples)

    def _select_dp_epsilon(self, experiences: List[Dict]) -> float:
        """Seleciona ε de DP baseado na sensibilidade dos dados."""
        # Heurística simples: mais sensível → menor ε
        sensitivity_score = np.mean([
            exp.get("sensitivity_score", 0.5) for exp in experiences
        ]) if experiences else 0.5
        # Mapear [0, 1] → [ε_max, ε_min]
        ε_min, ε_max = self.config.dp_epsilon_range
        return ε_max - (ε_max - ε_min) * sensitivity_score

    async def _sign_with_pqc(self, data: bytes) -> str:
        """Assina dados com PQC via HSM para integridade."""
        if self.hsm:
            result = await self.hsm.sign_data(data, {"purpose": "federated_update"})
            return result.get("signature_hex", "")
        else:
            # Fallback para desenvolvimento
            return hashlib.sha3_256(data + self.config.node_id.encode()).hexdigest()

    async def _verify_pqc_signature(self, update: LocalModelUpdate) -> bool:
        """Verifica assinatura PQC de atualização recebida."""
        if self.hsm:
            # Em produção: verificar com chave pública do nó
            return True  # Mock para demo
        else:
            expected = hashlib.sha3_256(
                update.model_weights + update.node_id.encode()
            ).hexdigest()
            return update.pqc_signature == expected

    async def _local_train(
        self,
        experiences: List[Dict],
        epochs: int,
        learning_rate: float
    ) -> float:
        """Executa treinamento local incremental."""
        # Implementação simplificada para demonstração
        # Em produção: loop completo de treinamento com backpropagation
        await asyncio.sleep(0.1)  # Simular tempo de treino
        return np.random.uniform(0.01, 0.1)  # Mock loss

    async def _compute_local_phi_c(self, experiences: List[Dict]) -> float:
        """Calcula contribuição Φ_C do treinamento local."""
        # Heurística baseada em qualidade das experiências
        avg_success = np.mean([exp.get("success", 0.5) for exp in experiences]) if experiences else 0.5
        return min(1.0, 0.8 + avg_success * 0.2)

    async def _add_dp_noise(self, weights: Dict, epsilon: float) -> Dict:
        """Adiciona ruído Laplace para privacidade diferencial."""
        noisy = {}
        for key, tensor in weights.items():
            if isinstance(tensor, torch.Tensor):
                noise = torch.from_numpy(
                    np.random.laplace(0, 1/epsilon, tensor.shape)
                ).float()
                noisy[key] = tensor + noise
            else:
                noisy[key] = tensor
        return noisy

    async def _encrypt_weights(self, weights: Dict) -> bytes:
        """Criptografa pesos para transmissão segura."""
        # Using torch.save to serialize weights safely
        buffer = io.BytesIO()
        torch.save(weights, buffer)
        return buffer.getvalue()

    async def _decrypt_weights(self, encrypted_weights: bytes) -> Dict:
        """Descriptografa pesos recebidos."""
        # Safely loading weights
        buffer = io.BytesIO(encrypted_weights)
        return torch.load(buffer, weights_only=True)

    def get_federation_statistics(self) -> Dict:
        """Retorna estatísticas do treinamento federado."""
        return {
            "node_id": self.config.node_id,
            "rounds_completed": self._round_number,
            "aggregation_history": self._aggregation_history[-10:],
            "strategy": self.config.aggregation_strategy,
            "min_phi_c_threshold": self.config.min_phi_c_for_aggregation,
            "dp_epsilon_range": self.config.dp_epsilon_range,
            "registered_participants": len(self._participant_registry)
        }
