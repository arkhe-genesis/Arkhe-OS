"""
ADNI Validation Pipeline v1.0
Integração NeuralScaffold com dados reais ADNI
"""

import numpy as np
import pandas as pd
from scipy.io import loadmat
from pathlib import Path
from typing import Dict, List, Tuple
import json
from .neural_scaffold import NeuralScaffold, build_scaffold_from_dti, extract_omega_from_fmri, bold_to_phases
from scipy import stats

class ADNIValidator:
    """Pipeline de validação do NeuralScaffold contra dados ADNI"""

    def __init__(self, adni_root: Path, atlas: str = 'AAL'):
        self.adni_root = adni_root
        self.atlas = atlas
        self.results = []

    def load_subject(self, subject_id: str, visit: str = 'bl') -> Dict:
        """Carrega dados DTI e fMRI de um sujeito específico"""
        # Estrutura típica ADNI: subject_id/visit/modality
        dti_path = self.adni_root / f"{subject_id}/{visit}/dti/connectivity_{self.atlas}.mat"
        fmri_path = self.adni_root / f"{subject_id}/{visit}/fmri/timeseries_{self.atlas}.txt"
        clinical_path = self.adni_root / f"{subject_id}/clinical.json"

        data = {
            'conn_matrix': loadmat(dti_path)['connectivity'],
            'bold_series': np.loadtxt(fmri_path),
            'clinical': json.loads(clinical_path.read_text())
        }
        return data

    def process_subject(self, subject_data: Dict) -> Dict:
        """Processa um sujeito através do pipeline completo"""
        # 1. Constrói scaffold físico
        centroids = self._load_atlas_centroids()  # Coordenadas AAL
        scaffold = build_scaffold_from_dti(
            subject_data['conn_matrix'],
            centroids,
            velocity=5.0  # m/s, estimativa literatura
        )

        # 2. Extrai parâmetros dinâmicos do fMRI real
        if subject_data.get('bold_series') is not None:
            scaffold.omega = extract_omega_from_fmri(subject_data['bold_series'])
            scaffold.theta = bold_to_phases(subject_data['bold_series'])

        # 3. Calibra degradação se houver dados longitudinais (simplificado aqui)
        # Para baseline, assumimos degradação proporcional à idade e APOE4
        age = subject_data['clinical'].get('AGE', 75)
        apoe4 = subject_data['clinical'].get('APOE4', 0)
        base_degradation = self._estimate_baseline_degradation(age, apoe4)
        scaffold.apply_pathology(base_degradation)

        # 4. Simulação de equilibração (modelo encontra atração)
        for _ in range(100):
            scaffold.step(dt=0.05)

        # 5. Extração de métricas
        final_state = scaffold.history[-1]

        return {
            'subject_id': subject_data['clinical'].get('PTID', 'Unknown'),
            'mmse': subject_data['clinical'].get('MMSE'),
            'cdr_sb': subject_data['clinical'].get('CDR_SB'),
            'diagnosis': subject_data['clinical'].get('DX', 'Unknown'),
            'r_global': final_state.r_global,
            'X_eff_volume': final_state.X_eff_volume,
            'complexity_LZ': final_state.complexity_LZ,
            'phase': final_state.phase.name,
            'degradation_calibrated': base_degradation
        }

    def run_cohort_validation(self, subject_list: List[str]) -> pd.DataFrame:
        """Executa validação em toda a coorte"""
        for sid in subject_list:
            try:
                data = self.load_subject(sid)
                result = self.process_subject(data)
                self.results.append(result)
                print(f"Processado {sid}: r={result['r_global']:.3f}, "
                      f"MMSE={result['mmse']}, Fase={result['phase']}")
            except Exception as e:
                print(f"Erro em {sid}: {e}")

        return pd.DataFrame(self.results)

    def statistical_validation(self, df: pd.DataFrame) -> Dict:
        """Análise estatística das hipóteses H1-H3"""

        # H1: ANOVA entre grupos diagnósticos
        groups = [df[df['diagnosis'] == d]['r_global'].dropna().values for d in df['diagnosis'].unique()]
        if len(groups) >= 2:
            f_stat, p_val = stats.f_oneway(*groups)
        else:
            f_stat, p_val = 0.0, 1.0

        # H2/H3: Correlações
        corr_r_mmse, p_r = stats.spearmanr(df['r_global'], df['mmse'], nan_policy='omit')
        corr_x_cdr, p_x = stats.spearmanr(df['X_eff_volume'], df['cdr_sb'], nan_policy='omit')

        return {
            'H1_anova_f': f_stat,
            'H1_anova_p': p_val,
            'H2_corr_r_mmse': corr_r_mmse,
            'H2_p_value': p_r,
            'H3_corr_x_cdr': corr_x_cdr,
            'H3_p_value': p_x,
            'n_subjects': len(df)
        }

    def _load_atlas_centroids(self) -> np.ndarray:
        # Mocking centroids for base class
        return np.random.randn(90, 3) * 50

    def _estimate_baseline_degradation(self, age: float, apoe4: int) -> float:
        return max(0, min(1, (age - 60) / 40 + (0.1 if apoe4 > 0 else 0)))
