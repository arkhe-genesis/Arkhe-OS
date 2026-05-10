# portability_protocol.py — Protocolo de portabilidade universal

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

@dataclass
class PortabilityExport:
    citizen_id: str
    exported_at: float
    schema_version: str = "cathedral/portability/v1"
    payload: Dict[str, Any] = None
    signature: str = ""

class PortabilityProtocol:
    """
    Define o protocolo de exportação usando JSON-LD e assinaturas criptográficas Ed25519.
    """

    CATHEDRAL_CONTEXT = {
        "@context": {
            "@version": 1.1,
            "cathedral": "https://schema.cathedral.ark/",
            "CitizenData": "cathedral:CitizenData",
            "citizenId": "cathedral:citizenId",
            "timestamp": "schema:dateTime",
            "payload": "cathedral:payload",
            "signature": "cathedral:signature"
        }
    }

    def __init__(self):
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def export_data(self, citizen_id: str, data: Dict[str, Any], consent_manager: Any) -> Dict[str, Any]:
        """
        Exporta dados do cidadão respeitando o consentimento granular (Matriz).
        """
        filtered_data = {}

        # Mapeamento de campos para Categorias e Propósito de Portabilidade
        from dynamic_consent_protocol import DataCategory, Purpose

        mapping = {
            "biometrics": DataCategory.BIOMETRIC,
            "behavioral": DataCategory.BEHAVIORAL,
            "financial": DataCategory.FINANCIAL,
            "health": DataCategory.HEALTH,
            "location": DataCategory.LOCATION
        }

        # Para Portabilidade, usamos a finalidade SERVICE_PROVISION ou uma específica de Portabilidade se existisse
        purpose = Purpose.SERVICE_PROVISION

        for key, value in data.items():
            category = mapping.get(key)
            if category:
                if consent_manager.is_allowed(citizen_id, category, purpose):
                    filtered_data[key] = value
            else:
                filtered_data[key] = value

        export_id = hashlib.sha256(f"{citizen_id}_{time.time()}".encode()).hexdigest()[:12]

        json_ld_export = {
            **self.CATHEDRAL_CONTEXT,
            "@type": "CitizenData",
            "citizenId": citizen_id,
            "exportId": export_id,
            "exportedAt": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "payload": filtered_data
        }

        # Assinatura real usando Ed25519
        data_to_sign = json.dumps(json_ld_export, sort_keys=True).encode()
        signature = self.private_key.sign(data_to_sign)
        json_ld_export["signature"] = {
            "@type": "cathedral:Ed25519Signature",
            "value": signature.hex(),
            "publicKey": self.get_public_key_pem()
        }

        return json_ld_export

    def get_public_key_pem(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def validate_import(self, export_data: Dict[str, Any]) -> bool:
        """
        Valida a integridade e autenticidade de um export.
        """
        if "signature" not in export_data or "payload" not in export_data:
            return False

        sig_info = export_data["signature"]
        sig_value = bytes.fromhex(sig_info["value"])
        pub_key_pem = sig_info["publicKey"]

        # Reconstrói dados originais (remove assinatura para verificar)
        data_to_verify = {k: v for k, v in export_data.items() if k != "signature"}
        data_bytes = json.dumps(data_to_verify, sort_keys=True).encode()

        try:
            public_key = serialization.load_pem_public_key(pub_key_pem.encode())
            public_key.verify(sig_value, data_bytes)
            return True
        except Exception:
            return False
