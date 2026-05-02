#!/usr/bin/env python3
"""
Cliente para submissão de provas ZK ao OCTRA (On-Chain Truth Registry for ARKHE).
"""
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime

class OCTRAClient:
    """Cliente para submissão de provas ao OCTRA via API."""

    def __init__(self, api_endpoint: str = 'https://octra.arkhe.network/api/v1'):
        self.api_endpoint = api_endpoint
        self.session = requests.Session()

    def submit_proof(self,
                    proof_data: dict,
                    metadata: dict = None,
                    api_key: str = None) -> dict:
        """
        Submete prova ZK ao OCTRA para registro imutável.

        Args:
            proof_data: dicionário com dados da prova (hash, tamanho, etc.)
            metadata: metadados opcionais (timestamp, versão, fingerprint)
            api_key: chave de API para autenticação (opcional)

        Returns:
            dict com resposta do OCTRA (transaction_id, block_number, etc.)
        """
        # Preparar payload
        payload = {
            'proof_hash': proof_data.get('proof_hash'),
            'proof_size_bytes': proof_data.get('proof_size_bytes'),
            'community_id': proof_data.get('community_id'),
            'capture_fraction': proof_data.get('capture_fraction'),
            'cohesion_rho': proof_data.get('cohesion_rho'),
            'manifold_dim': proof_data.get('manifold_dim'),
            'epsilon': proof_data.get('epsilon'),
            'timestamp': datetime.now().isoformat(),
            'arkhe_version': 'v∞.327.7',
            'metadata': metadata or {}
        }

        # Headers com autenticação se fornecida
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        # Submeter via API
        response = self.session.post(
            f'{self.api_endpoint}/submit_proof',
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(f"OCTRA submission failed: {response.status_code} - {response.text}")

        return response.json()

    def verify_proof(self, proof_hash: str) -> dict:
        """
        Verifica status de uma prova submetida ao OCTRA.

        Args:
            proof_hash: hash da prova a verificar

        Returns:
            dict com status da verificação (confirmed, block_number, etc.)
        """
        response = self.session.get(
            f'{self.api_endpoint}/verify/{proof_hash}',
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(f"Verification failed: {response.status_code}")

        return response.json()
