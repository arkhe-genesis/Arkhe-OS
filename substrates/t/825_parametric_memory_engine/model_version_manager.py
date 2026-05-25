#!/usr/bin/env python3
"""
model_version_manager.py — Substrato 825.5
Pipeline de Snapshot para o Model Version Manager no Object Storage
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import torch
import torch.nn as nn
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError


@dataclass
class SnapshotConfig:
    """Configuração do pipeline de snapshot."""
    bucket_name: str = "arkhe-models"
    model_prefix: str = "pmg"
    region: str = "br-se1"
    endpoint_url: str = "https://object-storage.magalu.cloud"
    snapshot_interval_hours: float = 1.0
    error_threshold_for_snapshot: float = 0.05  # Snapshot se erro cai 5%


class ModelVersionManager:
    """
    Gerencia versões do modelo no Object Storage Magalu Cloud.
    Cria snapshots periódicos com selos SHA3-256.
    """

    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.s3 = boto3.client(
            's3',
            endpoint_url=config.endpoint_url,
            region_name=config.region,
        )
        self.current_version = 42  # Versão base
        self.last_error = float('inf')
        self.last_snapshot_time = 0.0

    def _compute_seal(self, model_data: bytes) -> str:
        """Computa selo SHA3-256 dos pesos do modelo."""
        return hashlib.sha3_256(model_data).hexdigest()

    def _version_path(self, version: int) -> str:
        """Retorna o caminho S3 para uma versão."""
        return f"{self.config.model_prefix}/v{version}/model.pt"

    def _seal_path(self, version: int) -> str:
        """Retorna o caminho S3 para o selo de uma versão."""
        return f"{self.config.model_prefix}/v{version}/seal.sha3"

    def _metadata_path(self, version: int) -> str:
        """Retorna o caminho S3 para metadados."""
        return f"{self.config.model_prefix}/v{version}/metadata.json"

    def create_snapshot(self, model: nn.Module, current_error: float) -> Optional[Dict]:
        """
        Cria um snapshot do modelo se as condições forem atendidas.
        Retorna metadados do snapshot ou None se não criado.
        """
        now = time.time()
        hours_since_last = (now - self.last_snapshot_time) / 3600.0
        error_improvement = self.last_error - current_error

        # Condições para snapshot:
        # 1. Intervalo mínimo atingido
        # 2. Melhoria significativa no erro
        should_snapshot = (
            hours_since_last >= self.config.snapshot_interval_hours or
            error_improvement >= self.config.error_threshold_for_snapshot
        )

        if not should_snapshot:
            return None

        # Serializar modelo
        import io
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        model_data = buffer.getvalue()

        # Computar selo
        seal = self._compute_seal(model_data)

        # Incrementar versão
        self.current_version += 1
        version = self.current_version

        # Upload para Object Storage
        try:
            # Upload modelo
            self.s3.put_object(
                Bucket=self.config.bucket_name,
                Key=self._version_path(version),
                Body=model_data,
                Metadata={'seal': seal},
            )

            # Upload selo
            self.s3.put_object(
                Bucket=self.config.bucket_name,
                Key=self._seal_path(version),
                Body=seal.encode('utf-8'),
            )

            # Upload metadados
            metadata = {
                "version": version,
                "timestamp": now,
                "seal": seal,
                "error_before": self.last_error,
                "error_after": current_error,
                "error_improvement": error_improvement,
                "model_size_bytes": len(model_data),
                "substrato": "825",
                "arkhe_seal": seal,
            }
            self.s3.put_object(
                Bucket=self.config.bucket_name,
                Key=self._metadata_path(version),
                Body=json.dumps(metadata, indent=2).encode('utf-8'),
                ContentType='application/json',
            )

            self.last_snapshot_time = now
            self.last_error = current_error

            print(f"[825.5] Snapshot v{version} created: {self._version_path(version)}")
            print(f"[825.5] Seal: {seal[:16]}...")
            print(f"[825.5] Error improvement: {error_improvement:.4f}")

            return metadata

        except ClientError as e:
            print(f"[825.5] ERROR creating snapshot: {e}")
            self.current_version -= 1  # Reverter incremento
            return None

    def load_version(self, version: int) -> Optional[Dict[str, torch.Tensor]]:
        """Carrega uma versão específica do modelo."""
        try:
            # Verificar selo
            seal_obj = self.s3.get_object(
                Bucket=self.config.bucket_name,
                Key=self._seal_path(version),
            )
            stored_seal = seal_obj['Body'].read().decode('utf-8')

            # Carregar modelo
            model_obj = self.s3.get_object(
                Bucket=self.config.bucket_name,
                Key=self._version_path(version),
            )
            model_data = model_obj['Body'].read()

            # Verificar integridade
            computed_seal = self._compute_seal(model_data)
            if computed_seal != stored_seal:
                raise ValueError(f"Seal mismatch! Stored: {stored_seal}, Computed: {computed_seal}")

            # Desserializar
            import io
            buffer = io.BytesIO(model_data)
            state_dict = torch.load(buffer, map_location='cpu')

            print(f"[825.5] Version v{version} loaded successfully. Seal verified.")
            return state_dict

        except ClientError as e:
            print(f"[825.5] ERROR loading version {version}: {e}")
            return None

    def list_versions(self) -> list:
        """Lista todas as versões disponíveis."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.config.bucket_name,
                Prefix=f"{self.config.model_prefix}/",
                Delimiter='/',
            )
            versions = []
            for prefix in response.get('CommonPrefixes', []):
                version_str = prefix['Prefix'].split('/')[-2]
                if version_str.startswith('v'):
                    versions.append(int(version_str[1:]))
            return sorted(versions)
        except ClientError as e:
            print(f"[825.5] ERROR listing versions: {e}")
            return []


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   MODEL VERSION MANAGER — SUBSTRATO 825.5                ║")
    print("║   Snapshot Pipeline | Object Storage Magalu | ξM-Field    ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Configuração
    config = SnapshotConfig(
        bucket_name="arkhe-models",
        model_prefix="pmg",
        region="br-se1",
        endpoint_url="https://object-storage.magalu.cloud",
    )

    mvm = ModelVersionManager(config)

    # Modelo de teste
    model = nn.Sequential(
        nn.Linear(768, 512),
        nn.ReLU(),
        nn.Linear(512, 256),
    )

    # Simular 5 snapshots com melhoria de erro
    for i in range(5):
        current_error = 0.5 - (i * 0.08)  # Erro decaindo
        metadata = mvm.create_snapshot(model, current_error)

        if metadata:
            print(f"✅ Snapshot v{metadata['version']} created (error={metadata['error_after']:.4f})\n")
        else:
            print(f"⏭️  Snapshot skipped (conditions not met)\n")

    # Listar versões
    versions = mvm.list_versions()
    print(f"📚 Available versions: {versions}")

    # Carregar versão mais recente
    if versions:
        latest = versions[-1]
        state_dict = mvm.load_version(latest)
        if state_dict:
            print(f"✅ Version v{latest} loaded and verified.")


if __name__ == "__main__":
    main()
