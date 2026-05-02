#!/usr/bin/env python3
"""
Loader para dados reais do Crystal Brain v∞.15 com validação de integridade.
"""
import numpy as np
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple

class CrystalBrainRealLoader:
    """Carrega e valida dados reais do Crystal Brain v∞.15."""

    def __init__(self,
                 data_dir: str = 'data/crystal_brain_v15',
                 expected_hash: Optional[str] = None):
        """
        Inicializa loader com verificação de integridade via SHA-256.

        Args:
            data_dir: diretório com arquivos de dados
            expected_hash: hash SHA-256 esperado para validação (opcional)
        """
        self.data_dir = Path(data_dir)
        self.expected_hash = expected_hash
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Carrega metadados do dataset com validação de fingerprint."""
        metadata_path = self.data_dir / 'metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path) as f:
            metadata = json.load(f)

        # Validar versão e fingerprint do ARKHE
        assert metadata['version'] == 'v∞.15', f"Wrong version: {metadata['version']}"
        assert abs(metadata['fingerprint'] - 0.58) < 1e-6, "Wrong fingerprint"

        return metadata

    def get_crystal_metadata(self):
        return {str(i): {} for i in range(768)}

    def load_phases(self,
                   n_timesteps: Optional[int] = None,
                   crystal_indices: Optional[list] = None,
                   validate_integrity: bool = True) -> np.ndarray:
        """
        Carrega fases dos cristais com validação opcional de integridade.

        Args:
            n_timesteps: número de amostras temporais (None = todas)
            crystal_indices: índices dos cristais a carregar (None = todos)
            validate_integrity: validar hash do arquivo via SHA-256

        Returns:
            array (n_timesteps, n_crystals) com fases φ ∈ [0, 2π)
        """
        phases_path = self.data_dir / 'phases.npy'

        # Validar integridade se solicitado
        if validate_integrity:
            self._validate_file_integrity(phases_path)

        # Carregar dados
        phases = np.load(phases_path)

        # Aplicar filtros
        if n_timesteps is not None:
            phases = phases[:n_timesteps]
        if crystal_indices is not None:
            phases = phases[:, crystal_indices]

        # Validar formato e range
        assert phases.ndim == 2, f"Expected 2D array, got {phases.ndim}D"
        assert np.all((phases >= 0) & (phases < 2*np.pi)), "Phases out of range [0, 2π)"

        return phases

    def _validate_file_integrity(self, filepath: Path):
        """Valida integridade de arquivo via hash SHA-256."""
        if not self.expected_hash:
            print(f"⚠️  Skipping integrity check: no expected hash provided")
            return

        print(f"🔐 Validating integrity of {filepath.name}...")

        # Calcular hash do arquivo
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        # Comparar com hash esperado
        if actual_hash != self.expected_hash:
            raise ValueError(
                f"❌ Integrity check FAILED for {filepath.name}:\n"
                f"  Expected: {self.expected_hash}\n"
                f"  Actual:   {actual_hash}\n"
                f"  Data may be corrupted or tampered with."
            )

        print(f"✓ Integrity verified: {actual_hash[:16]}...")
