#!/usr/bin/env python3
"""
ARKHE OS Substrato 202: Inter-Layer Hash Protocol SDK
Canon: ∞.Ω.∇+++.202.hash_protocol.sdk
Função: SDK para terceiros integrarem com protocolo de hash inter-camadas.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import hashlib
import json
import time
import requests

@dataclass
class HashEnvelope:
    """Envelope para envio de hash via SDK."""
    sender_layer: str
    receiver_layer: str
    namespace: str
    payload_hash: str
    metadata: Dict
    signature: Optional[str] = None
    priority: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)

class ArkheHashProtocolSDK:
    """
    SDK para integração com protocolo de hash inter-camadas.

    Uso básico:
    ```python
    sdk = ArkheHashProtocolSDK(endpoint="http://localhost:8080")

    # Enviar hash
    envelope = sdk.create_envelope(
        sender="my_service",
        receiver="beaver_logic",
        namespace="custom_txn",
        payload={"txn_id": "123", "amount": 100}
    )
    result = sdk.send(envelope)

    # Verificar cadeia
    is_valid = sdk.verify_chain([envelope1, envelope2])
    ```
    """

    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def create_envelope(
        self,
        sender: str,
        receiver: str,
        namespace: str,
        payload: Dict,
        metadata: Optional[Dict] = None,
        priority: int = 1
    ) -> HashEnvelope:
        """Cria envelope canônico a partir de payload arbitrário."""
        # Serializar payload canonicamente
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha3_256(payload_json.encode()).hexdigest()

        return HashEnvelope(
            sender_layer=sender,
            receiver_layer=receiver,
            namespace=namespace,
            payload_hash=payload_hash,
            metadata=metadata or {},
            priority=priority
        )

    def send(self, envelope: HashEnvelope, timeout: int = 30) -> Dict:
        """Envia envelope para o endpoint do protocolo."""
        url = f"{self.endpoint}/api/v1/hash/submit"

        response = self.session.post(
            url,
            json=envelope.to_dict(),
            timeout=timeout
        )
        response.raise_for_status()

        return response.json()

    def verify_chain(self, envelopes: List[HashEnvelope]) -> bool:
        """Verifica integridade de cadeia de hashes."""
        url = f"{self.endpoint}/api/v1/hash/verify-chain"

        response = self.session.post(
            url,
            json=[e.to_dict() for e in envelopes],
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get("valid", False)

    def get_namespace_info(self, namespace: str) -> Dict:
        """Obtém informações sobre um namespace de hash."""
        url = f"{self.endpoint}/api/v1/hash/namespaces/{namespace}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        """Verifica saúde do serviço de protocolo de hash."""
        url = f"{self.endpoint}/health"
        response = self.session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

# Exemplo de uso
if __name__ == "__main__":
    # Configurar SDK
    sdk = ArkheHashProtocolSDK(endpoint="http://localhost:8080")

    # Criar envelope para transação customizada
    envelope = sdk.create_envelope(
        sender="external_system",
        receiver="token_arkhe",
        namespace="payment",
        payload={
            "from": "ACC-001",
            "to": "ACC-002",
            "amount": 1500.00,
            "currency": "USDC"
        },
        metadata={"source": "legacy_cobol", "program": "BANK-TRANSFER"}
    )

    print(f"📦 Envelope criado:")
    print(f"   Namespace: {envelope.namespace}")
    print(f"   Payload Hash: {envelope.payload_hash[:16]}...")
    print(f"   Priority: {envelope.priority}")

    # Enviar (mock: endpoint pode não estar disponível)
    try:
        # result = sdk.send(envelope)
        print(f"✅ Envelope enviado: mock_success")
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Endpoint não disponível (esperado em ambiente de desenvolvimento)")

    # Verificar saúde
    try:
        # health = sdk.health_check()
        print(f"🏥 Health check: mock_healthy")
    except:
        print(f"⚠️ Health check não disponível")
