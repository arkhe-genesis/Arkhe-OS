# arkhe_os/validation/experimental_harness/ingestors/susceptibility.py
"""Ingestor para dados de susceptibilidade magnética."""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any

class SusceptibilityIngestor:
    """Extrai métricas de susceptibilidade para validação do CVE-283.1 (expoente ν)."""

    def ingest(self, data_file: Path, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Espera um arquivo CSV com colunas: field (T), chi (emu/mol).
        Extrai o expoente crítico ν via ajuste da susceptibilidade na transição.
        """
        df = pd.read_csv(data_file)
        field = df['field'].values
        chi = df['chi'].values

        # Determinar campo crítico B_c (pico de dχ/dB)
        dchi = np.gradient(chi, field)
        B_c = field[np.argmax(np.abs(dchi))]

        # Ajustar lei de potência χ ∼ |B - B_c|^(-γ) e derivar ν ≈ γ/2
        mask = field > B_c
        if sum(mask) < 5:
            # Não há dados suficientes acima de B_c
            return {}

        log_field = np.log(np.abs(field[mask] - B_c))
        log_chi = np.log(chi[mask])

        # Regressão linear para obter γ
        coeff = np.polyfit(log_field, log_chi, 1)
        gamma = abs(coeff[0])
        nu = gamma / 2.0   # Relação de scaling: γ = 2ν (classe Ising)

        # Incerteza estimada pelo erro padrão da regressão
        residuals = log_chi - np.polyval(coeff, log_field)
        std_err = np.sqrt(np.sum(residuals**2) / (len(residuals) - 2))
        nu_error = std_err / 2.0

        return {
            "CVE-283.1": {
                "value": nu,
                "error": nu_error,
                "metadata": {
                    "critical_field": B_c,
                    "gamma": gamma,
                    "points_fit": int(sum(mask))
                }
            }
        }