# fret_reader.py
"""
Módulo para carregamento e processamento de dados experimentais de FRET.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def load_fret_data(
    csv_file: str,
    phase_column: str = 'phase_rad',
    fret_column: str = 'fret_ratio',
    normalize: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Carrega dados experimentais de FRET de um arquivo CSV.
    """
    path = Path(csv_file)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_file}")

    logger.info(f"Carregando dados de: {csv_file}")
    df = pd.read_csv(csv_file)

    # Validar colunas
    required_columns = [phase_column, fret_column]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas não encontradas: {missing}")

    phases = df[phase_column].values
    fret = df[fret_column].values

    # Remover NaN
    mask = ~(np.isnan(phases) | np.isnan(fret))
    phases = phases[mask]
    fret = fret[mask]

    # Normalizar se solicitado
    if normalize:
        fret_min, fret_max = fret.min(), fret.max()
        if fret_max > fret_min:
            fret = (fret - fret_min) / (fret_max - fret_min)
        logger.info(f"Dados normalizados: [{fret_min:.3f}, {fret_max:.3f}]")

    logger.info(f"Carregados {len(phases)} pontos de dados")

    return phases, fret


def calibrate_noise(fret_signal: np.ndarray) -> Dict[str, float]:
    """
    Estima o nível de ruído do sinal FRET.
    """
    # Desvio padrão das diferenças consecutivas
    diffs = np.diff(fret_signal)
    noise_std = np.std(diffs)

    # Relação sinal-ruído
    signal_mean = np.mean(fret_signal)
    snr = signal_mean / (noise_std + 1e-10)

    # Percentis para detecção de outliers
    q75, q25 = np.percentile(fret_signal, [75, 25])
    iqr = q75 - q25

    return {
        "noise_std": noise_std,
        "snr": snr,
        "iqr": iqr,
        "signal_mean": signal_mean,
        "signal_std": np.std(fret_signal)
    }


def filter_outliers(
    phases: np.ndarray,
    fret_values: np.ndarray,
    method: str = 'iqr',
    threshold: float = 1.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove outliers do sinal FRET.
    """
    if method == 'iqr':
        q75, q25 = np.percentile(fret_values, [75, 25])
        iqr = q75 - q25
        lower = q25 - threshold * iqr
        upper = q75 + threshold * iqr
        mask = (fret_values >= lower) & (fret_values <= upper)
    elif method == 'zscore':
        z_scores = np.abs((fret_values - np.mean(fret_values)) / np.std(fret_values))
        mask = z_scores < threshold
    else:
        raise ValueError(f"Método desconhecido: {method}")

    filtered_phases = phases[mask]
    filtered_fret = fret_values[mask]

    removed = len(phases) - len(filtered_phases)
    logger.info(f"Removidos {removed} outliers ({100*removed/len(phases):.1f}%)")

    return filtered_phases, filtered_fret


def interpolate_missing(
    phases: np.ndarray,
    fret_values: np.ndarray,
    target_range: Tuple[float, float, int]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpola dados para preencher lacunas e padronizar resolução.
    """
    from scipy.interpolate import interp1d

    # Ordenar por fase
    sort_idx = np.argsort(phases)
    phases_sorted = phases[sort_idx]
    fret_sorted = fret_values[sort_idx]

    # Criar função de interpolação
    interp_func = interp1d(
        phases_sorted, fret_sorted,
        kind='linear',
        bounds_error=False,
        fill_value='extrapolate'
    )

    # Gerar range padronizado
    target_phases = np.linspace(*target_range)
    target_fret = interp_func(target_phases)

    logger.info(f"Interpolado para {len(target_phases)} pontos")

    return target_phases, target_fret


def load_and_preprocess(
    csv_file: str,
    remove_outliers: bool = True,
    interpolate_to: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Pipeline completo de carregamento e pré-processamento.
    """
    # Carregar
    phases, fret = load_fret_data(csv_file)

    # Calibrar ruído
    noise_metrics = calibrate_noise(fret)
    logger.info(f"SNR: {noise_metrics['snr']:.2f}, Ruído: {noise_metrics['noise_std']:.4f}")

    # Remover outliers se solicitado
    if remove_outliers:
        phases, fret = filter_outliers(phases, fret, method='iqr', threshold=1.5)

    # Interpolar se solicitado
    if interpolate_to:
        phases, fret = interpolate_missing(
            phases, fret,
            target_range=(phases.min(), phases.max(), interpolate_to)
        )

    return phases, fret
