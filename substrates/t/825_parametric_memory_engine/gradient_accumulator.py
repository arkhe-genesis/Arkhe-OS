#!/usr/bin/env python3
"""
gradient_accumulator.py — Substrato 825.1
Gradient Accumulator: buffer local com políticas de disparo
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import torch
import torch.nn as nn
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from collections import deque
import time
import threading
import json


@dataclass
class AccumulatorConfig:
    """Configuração do buffer de gradientes."""
    max_buffer_size: int = 32          # Máximo de interações antes de disparar
    max_wait_seconds: float = 30.0     # Timeout para disparo mesmo com buffer parcial
    min_gradient_norm: float = 1e-6    # Norma mínima para aceitar gradiente
    learning_rate: float = 1e-4        # LR para SGD local
    optimizer_type: str = "adam"       # adam | sgd | rmsprop
    loss_fn: str = "cross_entropy"     # Função de perda padrão


@dataclass
class Interaction:
    """Uma interação (entrada, saída, feedback) que gera um gradiente."""
    input_data: torch.Tensor
    model_output: torch.Tensor
    target: Optional[torch.Tensor] = None
    reward: float = 0.0                # Reforço: +1.0 (bom), -1.0 (ruim)
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    user_feedback: Optional[str] = None  # Texto de correção


class GradientAccumulator:
    """
    Buffer local que acumula interações e dispara atualizações
    de peso quando atinge critérios de tamanho ou timeout.
    """

    def __init__(self, model: nn.Module, config: AccumulatorConfig):
        self.model = model
        self.config = config
        self.buffer: deque[Interaction] = deque(maxlen=config.max_buffer_size)
        self.optimizer = self._create_optimizer()
        self.loss_function = self._create_loss_fn()
        self._lock = threading.RLock()
        self._last_update = time.time()
        self._update_count = 0
        self._gradient_history: List[float] = []

    def _create_optimizer(self):
        if self.config.optimizer_type == "adam":
            return torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        elif self.config.optimizer_type == "sgd":
            return torch.optim.SGD(self.model.parameters(), lr=self.config.learning_rate)
        elif self.config.optimizer_type == "rmsprop":
            return torch.optim.RMSprop(self.model.parameters(), lr=self.config.learning_rate)
        else:
            raise ValueError(f"Optimizer {self.config.optimizer_type} not supported")

    def _create_loss_fn(self):
        if self.config.loss_fn == "cross_entropy":
            return nn.CrossEntropyLoss()
        elif self.config.loss_fn == "mse":
            return nn.MSELoss()
        elif self.config.loss_fn == "nll":
            return nn.NLLLoss()
        else:
            raise ValueError(f"Loss function {self.config.loss_fn} not supported")

    def add_interaction(self, interaction: Interaction) -> bool:
        """
        Adiciona uma interação ao buffer. Retorna True se o disparo
        foi acionado (buffer cheio ou timeout).
        """
        with self._lock:
            self.buffer.append(interaction)
            should_trigger = (
                len(self.buffer) >= self.config.max_buffer_size or
                (time.time() - self._last_update) >= self.config.max_wait_seconds
            )
            if should_trigger:
                self._trigger_update()
                return True
            return False

    def _trigger_update(self):
        """Dispara o passo de gradiente local."""
        if len(self.buffer) == 0:
            return

        self.optimizer.zero_grad()
        total_loss = 0.0
        valid_gradients = 0

        for interaction in self.buffer:
            loss = self._compute_loss(interaction)
            if loss is not None:
                loss.backward()
                total_loss += loss.item()
                valid_gradients += 1

        if valid_gradients > 0:
            # Clip gradients para estabilidade
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            self._update_count += 1
            self._last_update = time.time()
            self._gradient_history.append(total_loss / valid_gradients)

        # Limpar buffer após atualização
        self.buffer.clear()

    def _compute_loss(self, interaction: Interaction) -> Optional[torch.Tensor]:
        """Computa a perda para uma interação."""
        if interaction.target is not None:
            # Supervised learning
            return self.loss_function(interaction.model_output, interaction.target)
        elif interaction.reward != 0.0:
            # Reinforcement learning (policy gradient simplificado)
            # Maximizar log-probabilidade ponderada pela recompensa
            log_probs = torch.log_softmax(interaction.model_output, dim=-1)
            # Simplificação: usar a recompensa como peso da perda
            return -interaction.reward * log_probs.mean()
        elif interaction.user_feedback is not None:
            # Aprendizado por feedback textual (simplificado)
            # Em produção, usar modelo de correção para gerar target
            return None  # Stub: requer implementação específica
        return None

    def get_state(self) -> dict:
        """Retorna estado serializável do acumulador."""
        return {
            "update_count": self._update_count,
            "last_update": self._last_update,
            "buffer_size": len(self.buffer),
            "gradient_history": self._gradient_history[-10:],  # Últimos 10
            "config": {
                "max_buffer_size": self.config.max_buffer_size,
                "max_wait_seconds": self.config.max_wait_seconds,
                "learning_rate": self.config.learning_rate,
            }
        }

    def export_parameter_delta(self) -> dict:
        """
        Exporta os pesos atualizados como um delta para o GAS.
        Retorna dict com tensores serializados (base64).
        """
        import base64
        import io

        delta = {}
        for name, param in self.model.named_parameters():
            buffer = io.BytesIO()
            torch.save(param.data, buffer)
            delta[name] = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "model_version": "v42",  # Versão base
            "delta": delta,
            "update_count": self._update_count,
            "timestamp": time.time(),
            "pod_id": "pme-pod-local",  # Substituir pelo Pod real
        }


def main():
    """Demonstração do Gradient Accumulator."""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   GRADIENT ACCUMULATOR — SUBSTRATO 825.1                  ║")
    print("║   Parametric Memory Engine | ξM-Field Local Learning      ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Modelo simples para demonstração
    model = nn.Sequential(
        nn.Linear(768, 512),
        nn.ReLU(),
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
    )

    config = AccumulatorConfig(
        max_buffer_size=8,
        max_wait_seconds=10.0,
        learning_rate=1e-4,
    )

    accumulator = GradientAccumulator(model, config)

    # Simular 20 interações
    for i in range(20):
        input_tensor = torch.randn(1, 768)
        with torch.no_grad():
            output = model(input_tensor)

        interaction = Interaction(
            input_data=input_tensor,
            model_output=output,
            target=torch.randint(0, 128, (1,)),
            reward=1.0 if i % 3 == 0 else 0.0,
            session_id=f"session-{i:03d}",
        )

        triggered = accumulator.add_interaction(interaction)
        status = "🔄 UPDATE TRIGGERED" if triggered else "📥 buffered"
        print(f"Interaction {i+1:2d} | Buffer {len(accumulator.buffer)}/{config.max_buffer_size} | {status}")

    state = accumulator.get_state()
    print(f"\n✅ Accumulator state: {json.dumps(state, indent=2)}")
    print(f"✅ Total updates: {state['update_count']}")
    print(f"✅ Gradient history (last 5): {state['gradient_history'][-5:]}")


if __name__ == "__main__":
    main()
