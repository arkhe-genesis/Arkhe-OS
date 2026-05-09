#!/usr/bin/env python3
"""
criticality_validation.py
==========================================================
Subprojeto Arcano #41 — Fase 4: Validação de Criticalidade

Valida que a rede integrada de cristais de tempo + HARDCORE_LOOP
opera em criticalidade de fase, exibindo:
- Avalanches de spikes com distribuição de lei de potência P(s) ~ s^(-τ)
- Correlações temporais com expoente α
- Ordem de Kuramoto no limiar de sincronização (R ≈ 0.5-0.7)

Estes são os assinaturas de sistemas conscientes em modelos de
rede neural crítica (Beggs & Plenz, 2003; Shew & Plenz, 2013).

Arkhe(n) Framework v3.0 — Catedral Arkhe, 2026.
"""

import numpy as np
from scipy.stats import linregress, powerlaw
from scipy.signal import find_peaks
from typing import List, Dict, Tuple, Optional
# import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class CriticalityValidator:
    """Valida criticalidade de fase em redes neurais integradas."""

    def __init__(self, avalanche_threshold: float = 0.5, min_avalanche_size: int = 3):
        self.avalanche_threshold = avalanche_threshold  # Limiar para definir "atividade"
        self.min_avalanche_size = min_avalanche_size    # Tamanho mínimo de avalanche
        self.bins_log = np.logspace(0, 3, 30)  # Bins logarítmicos para ajuste de lei de potência

    def detect_avalanches(self, spike_raster: np.ndarray, dt_ms: float) -> List[int]:
        """
        Detecta avalanches de spikes na matriz raster (neurônios × tempo).

        Uma avalanche é um período contínuo de atividade acima do threshold,
        separado de outras avalanches por períodos de inatividade.
        """
        n_neurons, n_steps = spike_raster.shape
        total_activity = np.sum(spike_raster, axis=0)  # Atividade total por passo de tempo

        # Identificar períodos ativos vs inativos
        active = total_activity >= self.avalanche_threshold * n_neurons

        avalanches = []
        current_size = 0
        in_avalanche = False

        for t in range(n_steps):
            if active[t]:
                if not in_avalanche:
                    in_avalanche = True
                    current_size = 0
                # Contar spikes neste passo
                current_size += int(total_activity[t])
            else:
                if in_avalanche and current_size >= self.min_avalanche_size:
                    avalanches.append(current_size)
                in_avalanche = False
                current_size = 0

        # Capturar avalanche final se existir
        if in_avalanche and current_size >= self.min_avalanche_size:
            avalanches.append(current_size)

        return avalanches

    def fit_power_law(self, avalanche_sizes: List[int]) -> Dict[str, float]:
        """
        Ajusta distribuição de tamanhos de avalanches a lei de potência P(s) ~ s^(-τ).

        Retorna expoente τ, qualidade do ajuste (R²), e faixa de validade.
        """
        if len(avalanche_sizes) < 20:
            return {"tau": None, "r_squared": 0.0, "status": "insufficient_data"}

        sizes = np.array(avalanche_sizes)

        # Histograma logarítmico
        hist, bin_edges = np.histogram(sizes, bins=self.bins_log, density=True)
        bin_centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])

        # Filtrar bins com dados válidos
        valid = (hist > 0) & (bin_centers >= self.min_avalanche_size)
        if np.sum(valid) < 5:
            return {"tau": None, "r_squared": 0.0, "status": "insufficient_power_law_region"}

        # Ajuste linear em escala log-log: log(P) = -τ·log(s) + C
        log_s = np.log(bin_centers[valid])
        log_p = np.log(hist[valid])

        slope, intercept, r_value, p_value, std_err = linregress(log_s, log_p)
        tau = -slope

        return {
            "tau": tau,
            "r_squared": r_value**2,
            "p_value": p_value,
            "std_err": std_err,
            "n_avalanches": len(sizes),
            "size_range": (sizes.min(), sizes.max()),
            "status": "valid" if (1.3 <= tau <= 1.7 and r_value**2 > 0.8) else "non_critical"
        }

    def compute_temporal_correlation(self, spike_train: np.ndarray,
                                   max_lag_ms: int = 100) -> Dict[str, float]:
        """
        Computa função de autocorrelação temporal para extrair expoente α.

        Para sistemas críticos: C(τ) ~ τ^(-α) com α ≈ 1.0
        """
        if len(spike_train) < max_lag_ms * 2:
            return {"alpha": None, "status": "insufficient_data"}

        # Autocorrelação normalizada
        mean = np.mean(spike_train)
        std = np.std(spike_train)
        if std < 1e-10:
            return {"alpha": None, "status": "zero_variance"}

        correlations = []
        lags = np.arange(1, min(max_lag_ms, len(spike_train) // 4))

        for lag in lags:
            corr = np.corrcoef(spike_train[:-lag], spike_train[lag:])[0, 1]
            if not np.isnan(corr):
                correlations.append((lag, corr))

        if len(correlations) < 10:
            return {"alpha": None, "status": "insufficient_correlation_points"}

        lags_arr = np.array([c[0] for c in correlations])
        corrs_arr = np.array([abs(c[1]) for c in correlations])

        # Ajuste de lei de potência em escala log-log
        valid = (corrs_arr > 0) & (lags_arr >= 5)
        if np.sum(valid) < 5:
            return {"alpha": None, "status": "insufficient_power_law_region"}

        log_lag = np.log(lags_arr[valid])
        log_corr = np.log(corrs_arr[valid])

        slope, _, r_value, _, _ = linregress(log_lag, log_corr)
        alpha = -slope

        return {
            "alpha": alpha,
            "r_squared": r_value**2,
            "lag_range": (lags_arr[valid].min(), lags_arr[valid].max()),
            "status": "valid" if (0.8 <= alpha <= 1.2 and r_value**2 > 0.7) else "non_critical"
        }

    def validate_criticality(self, spike_raster: np.ndarray,
                           dt_ms: float, global_omega: np.ndarray) -> Dict[str, any]:
        """
        Validação completa de criticalidade para rede integrada.

        Critérios de criticalidade (Shew & Plenz, 2013):
        1. τ ∈ [1.3, 1.7] para distribuição de tamanhos de avalanches
        2. α ∈ [0.8, 1.2] para correlações temporais
        3. R (ordem de Kuramoto) ∈ [0.5, 0.7] para sincronização crítica
        4. Branching ratio σ ≈ 1.0 (cada spike gera ~1 spike subsequente)
        """
        # 1. Detectar e analisar avalanches
        avalanches = self.detect_avalanches(spike_raster, dt_ms)
        power_law_fit = self.fit_power_law(avalanches)

        # 2. Analisar correlações temporais (agregar todos os neurônios)
        aggregate_spike_train = np.sum(spike_raster, axis=0)
        temporal_corr = self.compute_temporal_correlation(aggregate_spike_train)

        # 3. Calcular ordem de Kuramoto média
        avg_kuramoto_order = np.mean(global_omega)

        # 4. Estimar branching ratio (simplificado)
        branching_ratio = self._estimate_branching_ratio(spike_raster, dt_ms)

        # Avaliação final
        criticality_score = 0.0
        criteria_met = []

        if power_law_fit["status"] == "valid":
            criticality_score += 0.35
            criteria_met.append(f"τ = {power_law_fit['tau']:.2f} ∈ [1.3, 1.7]")

        if temporal_corr["status"] == "valid":
            criticality_score += 0.35
            criteria_met.append(f"α = {temporal_corr['alpha']:.2f} ∈ [0.8, 1.2]")

        if 0.5 <= avg_kuramoto_order <= 0.7:
            criticality_score += 0.15
            criteria_met.append(f"R = {avg_kuramoto_order:.2f} ∈ [0.5, 0.7]")

        if 0.9 <= branching_ratio <= 1.1:
            criticality_score += 0.15
            criteria_met.append(f"σ = {branching_ratio:.2f} ≈ 1.0")

        return {
            "criticality_score": criticality_score,
            "criteria_met": criteria_met,
            "is_critical": criticality_score >= 0.7,
            "power_law": power_law_fit,
            "temporal_correlation": temporal_corr,
            "kuramoto_order": avg_kuramoto_order,
            "branching_ratio": branching_ratio,
            "n_avalanches": len(avalanches),
            "recommendation": self._generate_recommendation(criticality_score, power_law_fit, temporal_corr)
        }

    def _estimate_branching_ratio(self, spike_raster: np.ndarray, dt_ms: float) -> float:
        """Estima branching ratio σ: spikes no tempo t+1 / spikes no tempo t."""
        total_spikes_per_step = np.sum(spike_raster, axis=0)

        # Evitar divisão por zero
        active_steps = total_spikes_per_step[:-1] > 0
        if np.sum(active_steps) < 10:
            return 1.0  # Default

        ratio = total_spikes_per_step[1:][active_steps] / total_spikes_per_step[:-1][active_steps]
        return np.median(ratio[np.isfinite(ratio)])

    def _generate_recommendation(self, score: float,
                               power_law: Dict,
                               temporal: Dict) -> str:
        """Gera recomendação baseada nos resultados da validação."""
        if score >= 0.85:
            return "✅ Sistema em criticalidade ótima. Pronto para biofeedback."
        elif score >= 0.7:
            return "⚠️ Sistema próximo da criticalidade. Ajustes finos recomendados."
        elif power_law.get("tau") and power_law["tau"] < 1.3:
            return "🔧 τ muito baixo: aumentar acoplamento ou reduzir threshold de OR."
        elif power_law.get("tau") and power_law["tau"] > 1.7:
            return "🔧 τ muito alto: reduzir acoplamento ou aumentar dissipação."
        elif temporal.get("alpha") and temporal["alpha"] < 0.8:
            return "🔧 α muito baixo: aumentar variabilidade de frequências naturais."
        elif temporal.get("alpha") and temporal["alpha"] > 1.2:
            return "🔧 α muito alto: reduzir ruído ou ajustar janela temporal."
        else:
            return "🔍 Dados insuficientes para diagnóstico. Aumentar duração da simulação."
