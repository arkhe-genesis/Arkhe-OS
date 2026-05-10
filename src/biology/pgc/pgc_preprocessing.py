import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PhaseConfig:
    p_value_threshold: float = 5e-8
    effect_column: str = 'BETA'
    se_column: str = 'SE'
    p_column: str = 'P'
    snp_column: str = 'SNP'
    chr_column: str = 'CHR'
    bp_column: str = 'BP'

class PGCPhaseTransformer:
    def __init__(self, config: PhaseConfig):
        self.config = config

    def calculate_phase(self, row):
        """
        Arkhe Phase Transformation v2.1
        theta = np.angle(beta + 1j * (1.0 / se**2))
        """
        try:
            beta = float(row[self.config.effect_column])
            p_val = float(row[self.config.p_column])
            se = float(row[self.config.se_column])

            if p_val <= 0: p_val = 1e-300

            # Inverse variance weighting
            weight = 1.0 / (se**2) if se > 0 else 0

            # Phase construction
            complex_val = beta + 1j * weight
            theta = np.angle(complex_val)

            return pd.Series([theta, weight, complex_val.real, complex_val.imag])
        except:
            return pd.Series([np.nan, np.nan, np.nan, np.nan])

    def process(self, input_path: Path, output_path: Path):
        logger.info(f"Processing GWAS stats: {input_path}")
        df = pd.read_csv(input_path, sep='\t')

        res = df.apply(self.calculate_phase, axis=1)
        df[['theta', 'weight', 'complex_real', 'complex_imag']] = res

        df = df.dropna(subset=['theta', 'weight'])

        # Parquet doesn't like complex types, so we store real/imag separately
        df.to_parquet(output_path)
        return df
