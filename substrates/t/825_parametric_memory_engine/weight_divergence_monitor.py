#!/usr/bin/env python3
"""
weight_divergence_monitor.py — Substrato 825.3
Monitor de Divergência de Pesos com Ghost Threshold Paramétrico
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time
import json


@dataclass
class DivergenceConfig:
    """Configuração do monitor de divergência."""
    ghost_threshold: float = 0.55      # γ paramétrico (diferente do γ de carga = 0.577)
    check_interval_seconds: float = 60.0
    divergence_metric: str = "l2"      # l2 | cosine | max
    warmup_steps: int = 10             # Passos antes de começar a monitorar


class WeightDivergenceMonitor:
    """
    Monitora a divergência entre pesos locais e o consenso global.
    Quando a divergência excede γ, o Pod é marcado para resync.
    """

    def __init__(self, model: nn.Module, config: DivergenceConfig):
        self.model = model
        self.config = config
        self.consensus_weights: Dict[str, torch.Tensor] = {}
        self.divergence_history: List[float] = []
        self.step_count = 0
        self.is_divergent = False
        self.resync_requested = False

    def update_consensus(self, consensus_state: Dict[str, torch.Tensor]):
        """Atualiza os pesos de consenso de referência."""
        self.consensus_weights = {
            k: v.clone().detach() for k, v in consensus_state.items()
        }
        self.step_count = 0
        self.is_divergent = False
        self.resync_requested = False

    def compute_divergence(self) -> Tuple[float, Dict[str, float]]:
        """
        Computa a divergência entre pesos locais e consenso.
        Retorna: (divergência_global, divergência_por_camada)
        """
        if not self.consensus_weights:
            return 0.0, {}

        layer_divergences = {}
        total_divergence = 0.0
        total_params = 0

        for name, local_param in self.model.named_parameters():
            if name not in self.consensus_weights:
                continue

            consensus_param = self.consensus_weights[name]

            if self.config.divergence_metric == "l2":
                diff = (local_param - consensus_param).flatten()
                div = torch.norm(diff, p=2).item()
                # Normalizar pelo número de parâmetros
                div = div / np.sqrt(local_param.numel())
            elif self.config.divergence_metric == "cosine":
                div = 1.0 - torch.cosine_similarity(
                    local_param.flatten(),
                    consensus_param.flatten(),
                    dim=0
                ).item()
            elif self.config.divergence_metric == "max":
                div = torch.max(torch.abs(local_param - consensus_param)).item()
            else:
                raise ValueError(f"Unknown metric: {self.config.divergence_metric}")

            layer_divergences[name] = div
            total_divergence += div * local_param.numel()
            total_params += local_param.numel()

        global_divergence = total_divergence / total_params if total_params > 0 else 0.0
        return global_divergence, layer_divergences

    def check_divergence(self) -> Dict:
        """
        Verifica se a divergência excede o Ghost Threshold.
        Retorna dict com status e métricas.
        """
        self.step_count += 1

        if self.step_count < self.config.warmup_steps:
            return {
                "status": "warming_up",
                "step": self.step_count,
                "warmup_target": self.config.warmup_steps,
            }

        global_div, layer_divs = self.compute_divergence()
        self.divergence_history.append(global_div)

        # Manter apenas últimas 100 medições
        if len(self.divergence_history) > 100:
            self.divergence_history = self.divergence_history[-100:]

        self.is_divergent = global_div > self.config.ghost_threshold

        if self.is_divergent and not self.resync_requested:
            self.resync_requested = True
            status = "DIVERGENT_RESYNC_REQUIRED"
        elif self.is_divergent:
            status = "DIVERGENT_RESYNC_PENDING"
        else:
            status = "COHERENT"
            self.resync_requested = False

        return {
            "status": status,
            "global_divergence": global_div,
            "ghost_threshold": self.config.ghost_threshold,
            "is_divergent": self.is_divergent,
            "resync_requested": self.resync_requested,
            "layer_divergences": {k: round(v, 6) for k, v in layer_divs.items()},
            "history_mean": np.mean(self.divergence_history) if self.divergence_history else 0.0,
            "history_std": np.std(self.divergence_history) if self.divergence_history else 0.0,
        }

    def should_serve_traffic(self) -> bool:
        """Retorna False se o Pod deve parar de servir tráfego."""
        return not (self.is_divergent and self.resync_requested)

    def get_state(self) -> dict:
        return {
            "step_count": self.step_count,
            "is_divergent": self.is_divergent,
            "resync_requested": self.resync_requested,
            "ghost_threshold": self.config.ghost_threshold,
            "divergence_history": [round(x, 6) for x in self.divergence_history[-10:]],
        }


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   WEIGHT DIVERGENCE MONITOR — SUBSTRATO 825.3           ║")
    print("║   Ghost Threshold Paramétrico | ξM-Field Coherence        ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Modelo de teste
    model = nn.Sequential(
        nn.Linear(768, 512),
        nn.ReLU(),
        nn.Linear(512, 256),
    )

    # Consenso inicial = pesos do modelo
    consensus = {name: param.clone().detach() for name, param in model.named_parameters()}

    config = DivergenceConfig(ghost_threshold=0.55, divergence_metric="l2")
    monitor = WeightDivergenceMonitor(model, config)
    monitor.update_consensus(consensus)

    # Simular 30 passos de treinamento local
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    for step in range(30):
        # Treinamento local (simulado)
        optimizer.zero_grad()
        x = torch.randn(4, 768)
        y = torch.randn(4, 256)
        loss = nn.MSELoss()(model(x), y)
        loss.backward()
        optimizer.step()

        # Verificar divergência
        result = monitor.check_divergence()

        icon = "🟢" if result["status"] == "COHERENT" else "🔴"
        print(f"Step {step+1:2d} | {icon} {result['status']:25s} | "
              f"div={result['global_divergence']:.4f} | threshold={config.ghost_threshold}")

        if result["status"] == "DIVERGENT_RESYNC_REQUIRED":
            print(f"\n🚨 RESYNC TRIGGERED: Pod must reload consensus weights!")
            # Simular resync
            monitor.update_consensus({name: param.clone().detach() for name, param in model.named_parameters()})
            print("✅ Resync complete. Pod can serve traffic again.\n")

    print(f"\n✅ Monitor state: {json.dumps(monitor.get_state(), indent=2)}")


if __name__ == "__main__":
    main()
