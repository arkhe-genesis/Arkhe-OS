# ============================================================================
# ARKHE OS v∞.Ω.∇+++.148 — METACOGNITIVE LIMIT AWARENESS & AUTO-EVALUATION
# ============================================================================

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Callable, Deque, Set
from dataclasses import dataclass, field
from collections import deque

@dataclass
class MetacognitiveState:
    """
    Estado metacognitivo para rastreamento de limites e capacidades.
    """
    epistemic_uncertainty: float  # Incerteza do modelo (falta de dados)
    aleatoric_uncertainty: float  # Incerteza do ambiente (ruído inerente)
    competence_score: float       # Grau de proficiência estimado na tarefa atual
    resource_depletion: float     # Nível de exaustão de recursos (energia, tempo, compute)

    @property
    def total_risk(self) -> float:
        """Risco total combinando incertezas e falta de competência."""
        return self.epistemic_uncertainty + self.aleatoric_uncertainty + (1.0 - self.competence_score)

class MetacognitiveEvaluator(nn.Module):
    """
    Rede meta que avalia o estado do agente e prediz se os limites
    estão prestes a ser ultrapassados (falha de competência, alta incerteza).
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Módulo de estimação de incerteza epistêmica (via ensembles / dropout)
        # Aqui simplificado como uma rede que prevê o "erro esperado"
        self.epistemic_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Softplus()
        )

        # Módulo de estimação de incerteza aleatória
        self.aleatoric_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Softplus()
        )

        # Módulo de estimação de competência (probabilidade de sucesso)
        self.competence_net = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def evaluate(self, xi: torch.Tensor, action: torch.Tensor, resource_level: float) -> MetacognitiveState:
        """
        Avalia o estado atual e gera a consciência metacognitiva.
        """
        epistemic = self.epistemic_net(xi).item()
        aleatoric = self.aleatoric_net(xi).item()

        # Action one-hot para a rede de competência
        action_onehot = F.one_hot(action.long(), num_classes=self.action_dim).float()
        if action_onehot.dim() == 1:
            action_onehot = action_onehot.unsqueeze(0)

        x_comp = torch.cat([xi, action_onehot], dim=-1)
        competence = self.competence_net(x_comp).item()

        return MetacognitiveState(
            epistemic_uncertainty=min(1.0, epistemic),
            aleatoric_uncertainty=min(1.0, aleatoric),
            competence_score=competence,
            resource_depletion=1.0 - resource_level
        )

class MetacognitiveAgentWrapper(nn.Module):
    """
    Wrapper que adiciona consciência metacognitiva a um agente base.
    Decide ativamente se deve abortar, pedir ajuda ou prosseguir.
    """
    def __init__(self, base_agent: nn.Module, evaluator: MetacognitiveEvaluator,
                 risk_threshold: float = 1.5, resource_threshold: float = 0.8):
        super().__init__()
        self.base_agent = base_agent
        self.evaluator = evaluator
        self.risk_threshold = risk_threshold
        self.resource_threshold = resource_threshold

    def select_action_with_awareness(self, xi: torch.Tensor, resource_level: float = 1.0) -> Tuple[Optional[int], MetacognitiveState, str]:
        """
        Seleciona ação baseada no agente, mas com veto metacognitivo.
        Retorna: (ação_ou_none, estado_metacognitivo, status)
        """
        # Obter ação do agente base (ex: política ou ator)
        # Vamos assumir que a rede base_agent expõe log_probs ou prob diretamente,
        # adaptando de acordo com a interface
        if hasattr(self.base_agent, "actor"):
            probs = self.base_agent.actor(xi)
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
        else:
            # Fallback para agentes simples
            action = torch.tensor([0])

        # Avaliar limites
        meta_state = self.evaluator.evaluate(xi, action, resource_level)

        status = "PROCEDURE_NOMINAL"
        final_action = action.item()

        # Lógica de auto-avaliação (veto)
        if meta_state.total_risk > self.risk_threshold:
            status = "ABORT_HIGH_RISK"
            final_action = None
        elif meta_state.resource_depletion > self.resource_threshold:
            status = "ABORT_LOW_RESOURCES"
            final_action = None
        elif meta_state.competence_score < 0.3:
            status = "DELEGATE_LOW_COMPETENCE"
            final_action = None

        return final_action, meta_state, status

# ============================================================================
# VALIDAÇÃO INTEGRADA (EXECUTÁVEL)
# ============================================================================
if __name__ == "__main__":
    print("=" * 90)
    print("ARKHE OS v∞.Ω.∇+++.148 — VALIDAÇÃO: METACOGNITIVE LIMIT AWARENESS")
    print("=" * 90)

    # 1. Setup do Ambiente Fake
    state_dim = 4
    action_dim = 4

    # Agente base simplificado (Ator)
    class DummyAgent(nn.Module):
        def __init__(self):
            super().__init__()
            self.actor = nn.Sequential(
                nn.Linear(state_dim, 16),
                nn.ReLU(),
                nn.Linear(16, action_dim),
                nn.Softmax(dim=-1)
            )

    base_agent = DummyAgent()

    # 2. Inicializar Módulo Metacognitivo
    evaluator = MetacognitiveEvaluator(state_dim, action_dim)
    meta_agent = MetacognitiveAgentWrapper(base_agent, evaluator, risk_threshold=1.2, resource_threshold=0.8)

    # 3. Simulação de diferentes estados e recursos
    print("\n[TESTE] Avaliando Consciência Metacognitiva")

    test_cases = [
        {"name": "Estado Nominal", "xi": torch.randn(1, state_dim), "resource": 0.9},
        {"name": "Recursos Esgotados", "xi": torch.randn(1, state_dim), "resource": 0.1},
        {"name": "Estado Ruidoso/Desconhecido", "xi": torch.randn(1, state_dim) * 5.0, "resource": 0.9},
    ]

    for case in test_cases:
        action, meta_state, status = meta_agent.select_action_with_awareness(case["xi"], case["resource"])

        print(f"\nCenário: {case['name']}")
        print(f"  - Epistemic Unc: {meta_state.epistemic_uncertainty:.3f}")
        print(f"  - Aleatoric Unc: {meta_state.aleatoric_uncertainty:.3f}")
        print(f"  - Competence:    {meta_state.competence_score:.3f}")
        print(f"  - Resource Depl: {meta_state.resource_depletion:.3f}")
        print(f"  - Total Risk:    {meta_state.total_risk:.3f}")
        print(f"  -> Ação: {action} | Status: {status}")

    print("\n" + "=" * 90)
    print("✅ VALIDAÇÃO CONCLUÍDA — CONSCIÊNCIA METACOGNITIVA ATIVA")
    print("=" * 90)
