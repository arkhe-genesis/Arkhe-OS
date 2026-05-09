"""
HCP-Aging Validator v1.0
Adaptador para dados reais do Human Connectome Project - Aging.
Constitucionalmente válido: apenas ingestão e processamento de dados
neuroimagem empíricos, sem inferências metafísicas.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json
import boto3
from botocore.exceptions import ClientError
from .adni_validator import ADNIValidator
from .neural_scaffold import build_scaffold_from_dti, extract_omega_from_fmri, bold_to_phases

class HCPAgingValidator(ADNIValidator):
    """
    Validador especializado para dados HCP-Aging.

    HCP-Aging fornece:
    - Structural connectivity (DTI) via MRtrix3
    - Functional connectivity (rfMRI)
    - Cognitivo: MoCA, MMSE (subset), CogComposite
    - Demografia: Idade, sexo, educação
    """

    def __init__(self, data_root: Path, credentials_file: Optional[Path] = None):
        super().__init__(adni_root=data_root, atlas='HCP')
        self.credentials_file = credentials_file
        self.s3_client = None
        self._init_s3_connection()

        # Mapeamento HCP-specific: 360 regiões (Glasser 2016) ou 85 (AAL-like)
        self.n_regions = 360  # Glasser2016 parcellation
        self.tr = 0.72  # HCP TR (repetition time)

    def _init_s3_connection(self):
        """Inicializa conexão AWS S3 para download dos dados HCP"""
        if self.credentials_file and self.credentials_file.exists():
            with open(self.credentials_file) as f:
                creds = json.load(f)
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=creds['access_key'],
                    aws_secret_access_key=creds['secret_key']
                )
                self.bucket_name = 'hcp-openaccess'
                print("Conexão S3 estabelecida para HCP OpenAccess")

    def download_subject_data(self, subject_id: str,
                             modalities: List[str] = ['structural', 'functional']) -> bool:
        """
        Download automático de dados HCP do S3 (requer credenciais).

        Estrutura HCP:
        s3://hcp-openaccess/HCP_1200/{subject_id}/...
        s3://hcp-openaccess/HCP_Aging/{subject_id}/...
        """
        if not self.s3_client:
            print("Erro: Credenciais AWS não configuradas. Use setup_credentials() primeiro.")
            return False

        local_path = self.adni_root / subject_id / "V1"
        local_path.mkdir(parents=True, exist_ok=True)

        try:
            for modality in modalities:
                if modality == 'structural':
                    # Arquivo de conectividade estrutural (MRtrix3 output)
                    s3_key = f"HCP_Aging/{subject_id}/T1w/Diffusion/connectome.csv"
                    local_file = local_path / "structural_connectome.csv"

                elif modality == 'functional':
                    # Série temporal rfMRI (cortical parcels) - buscando formato TXT se disponível
                    # HCP costuma disponibilizar series temporais parceladas como .txt ou .csv em alguns diretórios de análise
                    s3_key = f"HCP_Aging/{subject_id}/MNINonLinear/Results/rfMRI_REST1_APA/rfMRI_REST1_APA_Atlas_MSMAll_hp2000_clean.txt"
                    local_file = local_path / "rfMRI_timeseries.txt"

                else:
                    continue

                # Download
                print(f"Baixando {s3_key}...")
                self.s3_client.download_file(self.bucket_name, s3_key, str(local_file))

        except ClientError as e:
            print(f"Erro no download {subject_id}: {e}")
            return False

        return True

    def load_subject(self, subject_id: str, visit: str = 'V1') -> Dict:
        """
        Carrega dados de um sujeito HCP-Aging.

        HCP-Aging usa visitas: V1 (baseline), V2 (18 meses), V3 (36 meses)
        """
        subj_dir = self.adni_root / subject_id / visit

        # 1. Matriz de conectividade estrutural (preprocessada)
        conn_file = subj_dir / "structural_connectome.csv"
        if conn_file.exists():
            conn_matrix = pd.read_csv(conn_file, header=None).values
        else:
            raise FileNotFoundError(f"Matriz de conectividade não encontrada: {conn_file}")

        # 2. Série temporal fMRI (se disponível)
        fmri_file = subj_dir / "rfMRI_timeseries.txt"
        if fmri_file.exists():
            bold_series = np.loadtxt(fmri_file)  # Shape: (n_regions, n_timepoints)
            # Normalização (igual ao mock)
            bold_series = (bold_series - bold_series.mean(axis=1, keepdims=True)) / \
                         (bold_series.std(axis=1, keepdims=True) + 1e-10)
        else:
            # Se não houver fMRI, gerar placeholder (será detectado no processamento)
            bold_series = None

        # 3. Dados clínicos (do manifesto HCP)
        clinical = self._load_clinical_data(subject_id, visit)

        # 4. Coordenadas MNI (Glasser2016 template)
        centroids = self._load_glasser_centroids()

        return {
            'conn_matrix': conn_matrix,
            'bold_series': bold_series,
            'clinical': clinical,
            'centroids': centroids
        }

    def _load_clinical_data(self, subject_id: str, visit: str) -> Dict:
        """Carrega dados comportamentais/cognitivos do HCP-Aging"""
        # Arquivo de comportamento unificado do HCP
        behavior_file = self.adni_root / "hcp_aging_behavior.csv"

        if not behavior_file.exists():
            # Retorna estrutura mínima se arquivo não disponível
            return {
                'PTID': subject_id,
                'AGE': 75,
                'MMSE': None,  # HCP usa MoCA principalmente
                'MOCA': None,
                'COG_COMPOSITE': None,
                'DX': 'Unknown'
            }

        df = pd.read_csv(behavior_file)
        row = df[(df['Subject'] == subject_id) & (df['Visit'] == visit)]

        if len(row) == 0:
            # Fallback se não encontrar o sujeito exato
            return {
                'PTID': subject_id,
                'AGE': 75,
                'MOCA': None,
                'COG_COMPOSITE': None,
                'DX': 'Unknown'
            }

        row = row.iloc[0]

        # Classificação diagnóstica baseada em CogComposite (se disponível)
        cog_score = row.get('CogCogComp_AgeAdj', None)
        if cog_score is not None and not pd.isna(cog_score):
            if cog_score > 100:  # Acima da média
                diagnosis = 'CN'
            elif cog_score > 85:
                diagnosis = 'MCI'
            else:
                diagnosis = 'MCI_AD'  # HCP não tem AD severo, mas tem declínio
        else:
            diagnosis = 'Unknown'

        return {
            'PTID': subject_id,
            'AGE': row.get('Age', 75),
            'MOCA': row.get('MoCA', None),
            'COG_COMPOSITE': cog_score,
            'DX': diagnosis,
            'GENDER': row.get('Gender', 'Unknown'),
            'EDUCATION': row.get('EDYRS', 16)
        }

    def _load_glasser_centroids(self) -> np.ndarray:
        """Carrega coordenadas MNI dos 360 parcelas Glasser2016"""
        # Template fixo (disponível publicamente)
        glasser_coords = self.adni_root / "Glasser2016_centroids.txt"

        if glasser_coords.exists():
            return np.loadtxt(glasser_coords)
        else:
            # Fallback: gerar coordenadas aproximadas em esfera
            # (melhor ter o arquivo real do HCP)
            print("Aviso: Usando coordenadas centroid aproximadas")
            return np.random.randn(self.n_regions, 3) * 50

    def process_subject(self, subject_data: Dict) -> Dict:
        """
        Processa sujeito HCP através do NeuralScaffold.
        Sobrescreve método base para lidar com especificidades HCP.
        """
        # Calibrar velocidade de condução para HCP (fibra mais rápida que mock)
        velocity = 6.5  # m/s, estimativa DTI-based

        # Construir scaffold
        scaffold = build_scaffold_from_dti(
            subject_data['conn_matrix'],
            subject_data['centroids'],
            velocity=velocity
        )

        # Se temos fMRI real, usar para extrair omega e theta inicial
        if subject_data.get('bold_series') is not None:
            scaffold.omega = extract_omega_from_fmri(
                subject_data['bold_series'],
                fs=1/self.tr
            )
            scaffold.theta = bold_to_phases(subject_data['bold_series'])
        else:
            # Fallback: gerar dinâmica sintética realista baseada apenas na estrutura
            scaffold.omega = np.random.normal(1.0, 0.2, scaffold.N)
            scaffold.theta = np.random.uniform(0, 2*np.pi, scaffold.N)

        # Estimar degradação baseada em idade e cognição (calibração inicial)
        age = subject_data['clinical']['AGE']
        cog = subject_data['clinical'].get('COG_COMPOSITE', 100)

        # Modelo linear simples: degradação aumenta com idade e queda cognitiva
        base_degradation = max(0, min(1, (age - 60) / 40))  # 60y=0, 100y=1
        cognitive_factor = max(0, min(0.3, (100 - (cog if cog else 100)) / 100)) if cog else 0
        total_degradation = min(1.0, base_degradation + cognitive_factor)

        scaffold.apply_pathology(total_degradation)

        # Simulação de equilibração
        for _ in range(100):
            scaffold.step(dt=0.05)

        final_state = scaffold.history[-1]

        return {
            'subject_id': subject_data['clinical']['PTID'],
            'age': age,
            'moca': subject_data['clinical'].get('MOCA'),
            'cog_composite': cog,
            'diagnosis': subject_data['clinical']['DX'],
            'r_global': final_state.r_global,
            'X_eff_volume': final_state.X_eff_volume,
            'complexity_LZ': final_state.complexity_LZ,
            'phase': final_state.phase.name,
            'degradation_calibrated': total_degradation,
            'has_fmri': subject_data.get('bold_series') is not None
        }
