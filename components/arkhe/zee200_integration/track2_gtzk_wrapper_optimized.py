#!/usr/bin/env python3
"""
track2_gtzk_wrapper_optimized.py
Track 2 otimizado: MI estimator com bins reduzidos + sensor linear fallback.
"""
import numpy as np
from scipy import stats

def estimate_mutual_information_optimized(x, y, bins=20):
    """
    Estimador de MI otimizado:
    • Reduz bins de 40→20 (50% menos set_lookups)
    • Usa aproximação via correlação de rank se bins < 15
    """
    # Fallback para correlação de rank se bins muito baixo
    if bins < 15:
        # Spearman correlation como proxy para MI (mais barato)
        rho, _ = stats.spearmanr(x, y)
        # Aproximação: MI ≈ -0.5 * log(1 - rho²) para gaussiana
        return max(0, -0.5 * np.log(max(1e-10, 1 - rho**2)))

    # Histograma 2D com bins reduzidos
    hist_2d, _, _ = np.histogram2d(x, y, bins=bins)
    p_xy = hist_2d / np.sum(hist_2d)

    # Marginais
    p_x = np.sum(p_xy, axis=1)
    p_y = np.sum(p_xy, axis=0)

    # MI com epsilon para estabilidade numérica
    eps = 1e-12
    mi = 0.0
    for i in range(p_x.shape[0]):
        for j in range(p_y.shape[0]):
            if p_xy[i, j] > eps:
                mi += p_xy[i, j] * np.log(p_xy[i, j] / (p_x[i] * p_y[j] + eps) + eps)

    return max(0.0, mi)

def track2_gtzk_instruction_optimized(intention_signals, sensor_readings,
                                      sensor_params={'saturation_scale': 1.0, 'noise_std': 0.05},
                                      mi_bins=20):
    """
    Versão otimizada Track 2:
    • MI com bins=20 (reduz set_lookups em 50%)
    • Sensor linear se saturação > 0.9 (evita sigmoid caro)
    """
    # 1. Aplicar modelo de sensor (otimizado)
    sat = sensor_params['saturation_scale']
    noise_std = sensor_params['noise_std']

    # Fallback para sensor linear se saturação alta (evita sigmoid)
    if sat > 0.9:
        # Sensor linear: leitura = intenção × força + ruído
        predicted = np.array(intention_signals) * 0.8 + np.random.normal(0, noise_std, len(intention_signals))
    else:
        # Sigmoid completo
        predicted = 2.0 / (1.0 + np.exp(-np.clip(np.array(intention_signals) * 0.8 / sat, -5, 5))) - 1.0
        predicted += np.random.normal(0, noise_std, len(intention_signals))

    # 2. Calcular MI com bins otimizados
    mi_nats = estimate_mutual_information_optimized(intention_signals, sensor_readings, bins=mi_bins)

    # 3. Métricas adicionais (Pearson para fallback)
    r_pearson, p_raw = stats.pearsonr(intention_signals, sensor_readings)

    # 4. Constraints otimizadas
    constraints = [
        f"sensor_model: linear_or_sigmoid(sat={sat})",
        f"mi_estimator: histogram_2d(bins={mi_bins})",
        f"mi_nats = Σ p(x,y) log(p(x,y)/(p(x)p(y)))",
        f"mi_nats > 0.1 => informational_coupling_detected",
    ]

    # 5. Outputs públicos
    public_outputs = {
        'mi_nats': float(mi_nats),
        'pearson_r': float(r_pearson),
        'p_raw': float(p_raw),
        'mi_bins_used': float(mi_bins),
        'sensor_type': 1.0 if sat > 0.9 else 0.0,
        'interpretation': 1.0 if mi_nats > 0.1 else 0.0
    }

    # 6. Criar instrução GTZK real
    from track1_gtzk_wrapper_real import GTZKInstructionReal
    instruction = GTZKInstructionReal(
        name='track2_intention_coupling_opt',
        public_inputs={
            'n_trials': float(len(intention_signals)),
            'sat': float(sat),
            'noise_std': float(noise_std),
            'mi_bins': float(mi_bins)
        },
        private_witness={
            'sensor_readings': [float(x) for x in sensor_readings[:10]],  # Amostra para witness
            'predicted_sample': [float(x) for x in predicted[:10]],
        },
        constraints=constraints
    )

    return instruction, public_outputs
