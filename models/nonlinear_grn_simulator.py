#!/usr/bin/env python3
"""
Substrato 198-F: Nonlinear GRN Simulator
Modela redes regulatórias de genes com interações não-lineares,
epistase, feedbacks e dinâmicas temporais realistas.
"""
import asyncio
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Union
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionType(Enum):
    """Tipos de interação regulatória em GRN."""
    ACTIVATION = "activation"           # Ativação transcricional
    REPRESSION = "repression"           # Repressão transcricional
    COOPERATIVE_ACTIVATION = "coop_act" # Ativação cooperativa (Hill > 1)
    COMPETITIVE_REPRESSION = "comp_rep" # Repressão competitiva
    FEEDBACK_POSITIVE = "feedback_pos"  # Feedback positivo
    FEEDBACK_NEGATIVE = "feedback_neg"  # Feedback negativo
    EPISTASIS = "epistasis"             # Epistase (interação gene-gene)

@dataclass
class GRNInteraction:
    """Definição de uma interação regulatória na GRN."""
    source_gene: str
    target_gene: str
    interaction_type: InteractionType
    weight: float                       # Força da interação (-1 a +1)
    hill_coefficient: float = 1.0       # Cooperatividade (Hill coefficient)
    threshold: float = 0.5              # Threshold de ativação/repressão
    delay_minutes: float = 0.0          # Delay temporal (transcrição→tradução)
    degradation_rate: float = 0.1       # Taxa de degradação do alvo

@dataclass
class GRNState:
    """Estado dinâmico de uma rede regulatória de genes."""
    gene_expression: Dict[str, float]      # Nível de expressão atual [0, 1]
    protein_level: Dict[str, float]        # Nível de proteína traduzida [0, 1]
    last_update_time: float = 0.0
    external_signals: Dict[str, float] = field(default_factory=dict)

    def clone(self) -> 'GRNState':
        """Cria cópia profunda do estado."""
        return GRNState(
            gene_expression=self.gene_expression.copy(),
            protein_level=self.protein_level.copy(),
            last_update_time=self.last_update_time,
            external_signals=self.external_signals.copy()
        )

class NonlinearGRNSimulator:
    """
    Simulador de redes regulatórias de genes com dinâmicas não-lineares.

    Características:
    • Equações diferenciais com termos não-lineares (Hill functions)
    • Suporte a delays temporais (transcrição, tradução, transporte)
    • Epistase: interações gene-gene além de regulação direta
    • Ruído estocástico para modelar variabilidade biológica
    • Integração com sinais externos (campos vetoriais, atuadores)
    """

    # Parâmetros padrão para simulação
    DEFAULT_PARAMS = {
        "time_step_minutes": 1.0,          # Passo de integração
        "simulation_duration_hours": 24.0, # Duração total
        "noise_amplitude": 0.05,           # Ruído estocástico
        "min_expression": 0.0,             # Limite inferior de expressão
        "max_expression": 1.0,             # Limite superior de expressão
        "convergence_threshold": 1e-4,     # Critério de convergência
    }

    def __init__(
        self,
        interactions: List[GRNInteraction],
        initial_state: Optional[GRNState] = None,
        params: Optional[Dict] = None,
    ):
        self.interactions = {
            (i.source_gene, i.target_gene): i for i in interactions
        }
        self.state = initial_state or GRNState(gene_expression={}, protein_level={})
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self._interaction_cache: Dict[Tuple[str, str], Callable] = {}

    def _hill_function(self, x: float, k: float, n: float, activation: bool) -> float:
        """
        Função de Hill para modelar ativação/repressão não-linear.

        Args:
            x: Concentração do regulador
            k: Constante de dissociação (threshold)
            n: Coeficiente de Hill (cooperatividade)
            activation: True para ativação, False para repressão

        Returns:
            Fator de regulação [0, 1]
        """
        if activation:
            # Ativação: sigmoidal crescente
            return (x ** n) / (k ** n + x ** n)
        else:
            # Repressão: sigmoidal decrescente
            return k ** n / (k ** n + x ** n)

    def _compute_regulatory_input(
        self,
        target_gene: str,
        state: GRNState,
        time_minutes: float,
    ) -> float:
        """
        Calcula input regulatório total para um gene alvo.

        Considera:
        • Múltiplos reguladores com pesos diferentes
        • Interações não-lineares (Hill functions)
        • Delays temporais
        • Sinais externos
        """
        total_input = 0.0

        for (source, target), interaction in self.interactions.items():
            if target != target_gene:
                continue

            # Obter nível do regulador (proteína, com delay se aplicável)
            if interaction.delay_minutes > 0:
                # Em produção: usar buffer temporal para delays
                regulator_level = state.protein_level.get(source, 0.0)
            else:
                regulator_level = state.protein_level.get(source, 0.0)

            # Calcular efeito da interação
            if interaction.interaction_type == InteractionType.ACTIVATION:
                effect = self._hill_function(
                    regulator_level,
                    interaction.threshold,
                    interaction.hill_coefficient,
                    activation=True
                ) * interaction.weight

            elif interaction.interaction_type == InteractionType.REPRESSION:
                effect = self._hill_function(
                    regulator_level,
                    interaction.threshold,
                    interaction.hill_coefficient,
                    activation=False
                ) * interaction.weight

            elif interaction.interaction_type == InteractionType.COOPERATIVE_ACTIVATION:
                # Ativação cooperativa: múltiplos reguladores sinérgicos
                effect = (regulator_level ** interaction.hill_coefficient) * interaction.weight

            elif interaction.interaction_type == InteractionType.EPISTASIS:
                # Epistase: efeito depende de outro gene
                # Simplificado: produto dos níveis dos dois genes
                other_gene = [g for g in state.gene_expression.keys()
                             if g != source and g != target][0] if len(state.gene_expression) > 2 else source
                other_level = state.protein_level.get(other_gene, 0.5)
                effect = regulator_level * other_level * interaction.weight

            else:
                # Fallback: efeito linear
                effect = regulator_level * interaction.weight

            total_input += effect

        # Adicionar sinais externos (ex: campos vetoriais do P2I)
        external_signal = state.external_signals.get(target_gene, 0.0)
        total_input += external_signal * 0.3  # Peso moderado para sinais externos

        return np.clip(total_input, -2.0, 2.0)  # Limitar para estabilidade numérica

    def _update_gene_expression(
        self,
        gene: str,
        regulatory_input: float,
        state: GRNState,
        dt_minutes: float,
    ) -> float:
        """
        Atualiza expressão gênica usando equação diferencial simplificada.

        d[expr]/dt = basal_rate + regulatory_input - degradation * expr + noise
        """
        current_expr = state.gene_expression.get(gene, 0.1)

        # Parâmetros específicos do gene (em produção: carregar de banco de dados)
        basal_rate = 0.01
        degradation = self.interactions.get((gene, gene),
                                           GRNInteraction(gene, gene, InteractionType.REPRESSION, 0.1)).degradation_rate

        # Ruído estocástico (Gaussiano)
        noise = np.random.normal(0, self.params["noise_amplitude"])

        # Equação diferencial (Euler method)
        dexpr_dt = (
            basal_rate +
            regulatory_input * 0.1 -  # Escalar input para taxa de transcrição
            degradation * current_expr +
            noise
        )

        new_expr = current_expr + dexpr_dt * (dt_minutes / 60)  # Converter para horas

        # Aplicar limites
        return np.clip(new_expr,
                      self.params["min_expression"],
                      self.params["max_expression"])

    def _translate_to_protein(self, gene: str, mrna_level: float, dt_minutes: float) -> float:
        """Simula tradução de mRNA para proteína com delay."""
        current_protein = self.state.protein_level.get(gene, 0.0)

        # Parâmetros de tradução
        translation_rate = 0.05  # mRNA → proteína
        protein_degradation = 0.02

        # Equação simplificada
        dprotein_dt = translation_rate * mrna_level - protein_degradation * current_protein
        new_protein = current_protein + dprotein_dt * (dt_minutes / 60)

        return np.clip(new_protein, 0.0, 1.0)

    async def simulate(
        self,
        external_signal_fn: Optional[Callable[[float, str], float]] = None,
        callback: Optional[Callable[[float, GRNState], None]] = None,
    ) -> GRNState:
        """
        Executa simulação temporal da GRN.

        Args:
            external_signal_fn: Função que retorna sinal externo por gene ao longo do tempo
            callback: Callback para monitoramento em tempo real

        Returns:
            Estado final da GRN após simulação
        """
        total_steps = int(self.params["simulation_duration_hours"] * 60 / self.params["time_step_minutes"])

        for step in range(total_steps):
            current_time = step * self.params["time_step_minutes"]

            # Atualizar sinais externos se função fornecida
            if external_signal_fn:
                for gene in self.state.gene_expression.keys():
                    self.state.external_signals[gene] = external_signal_fn(current_time, gene)

            # Calcular inputs regulatórios para todos os genes
            regulatory_inputs = {}
            for gene in self.state.gene_expression.keys():
                regulatory_inputs[gene] = self._compute_regulatory_input(
                    gene, self.state, current_time
                )

            # Atualizar expressão gênica
            for gene in self.state.gene_expression.keys():
                self.state.gene_expression[gene] = self._update_gene_expression(
                    gene, regulatory_inputs[gene], self.state, self.params["time_step_minutes"]
                )

            # Atualizar níveis de proteína (tradução)
            for gene in self.state.gene_expression.keys():
                self.state.protein_level[gene] = self._translate_to_protein(
                    gene, self.state.gene_expression[gene], self.params["time_step_minutes"]
                )

            self.state.last_update_time = current_time

            # Callback para monitoramento
            if callback and step % 10 == 0:  # A cada 10 passos
                await asyncio.sleep(0)  # Permitir yield para async
                callback(current_time, self.state.clone())

            # Verificar convergência (opcional)
            if step > 100:  # Ignorar fase inicial transiente
                # Simplificado: verificar se mudanças são pequenas
                pass

        logger.info(f"✅ Simulação concluída: {total_steps} passos, {len(self.state.gene_expression)} genes")
        return self.state

    def get_state_summary(self, state: Optional[GRNState] = None) -> Dict:
        """Retorna resumo estatístico do estado da GRN."""
        if state is None:
            state = self.state

        if not state.gene_expression:
            return {}

        expr_values = list(state.gene_expression.values())
        protein_values = list(state.protein_level.values())

        return {
            "genes_count": len(state.gene_expression),
            "expression_stats": {
                "mean": np.mean(expr_values),
                "std": np.std(expr_values),
                "min": np.min(expr_values),
                "max": np.max(expr_values),
            },
            "protein_stats": {
                "mean": np.mean(protein_values),
                "std": np.std(protein_values),
                "min": np.min(protein_values),
                "max": np.max(protein_values),
            },
            "highly_expressed": [
                gene for gene, expr in state.gene_expression.items()
                if expr > 0.7
            ],
            "repressed": [
                gene for gene, expr in state.gene_expression.items()
                if expr < 0.2
            ],
            "last_update_time": state.last_update_time,
        }

    @staticmethod
    def build_memory_consolidation_grn() -> List[GRNInteraction]:
        """Constrói GRN de referência para consolidação de memória."""
        return [
            # CREB como hub central de plasticidade
            GRNInteraction("external_signal", "CREB1", InteractionType.ACTIVATION, 0.8, hill_coefficient=2.0),
            GRNInteraction("CREB1", "FOS", InteractionType.ACTIVATION, 0.7, threshold=0.3),
            GRNInteraction("CREB1", "EGR1", InteractionType.ACTIVATION, 0.65, threshold=0.3),
            GRNInteraction("CREB1", "BDNF", InteractionType.ACTIVATION, 0.6, threshold=0.4),
            GRNInteraction("CREB1", "ARC", InteractionType.ACTIVATION, 0.55, threshold=0.4),

            # Feedbacks e interações secundárias
            GRNInteraction("FOS", "BDNF", InteractionType.ACTIVATION, 0.4),
            GRNInteraction("ARC", "FOS", InteractionType.REPRESSION, -0.3, threshold=0.6),  # Feedback negativo
            GRNInteraction("BDNF", "CREB1", InteractionType.FEEDBACK_POSITIVE, 0.2),  # Loop positivo
            GRNInteraction("EGR1", "ARC", InteractionType.ACTIVATION, 0.3),

            # Epistase: interação sinérgica entre FOS e EGR1
            GRNInteraction("FOS", "SYN1", InteractionType.EPISTASIS, 0.5),
            GRNInteraction("EGR1", "SYN1", InteractionType.EPISTASIS, 0.5),
        ]
