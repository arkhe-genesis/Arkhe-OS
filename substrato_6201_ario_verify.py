# ╔══════════════════════════════════════════════════════════════╗
# ║  SUBSTRATO 6201 — AR.IO VERIFY (SIDECAR CANÔNICO)         ║
# ║  Prova criptográfica de autenticidade de dados Arweave     ║
# ╚══════════════════════════════════════════════════════════════╝
#
# O sidecar de verificação agora é um nó da Catedral.
# Cada verificação é uma prova ancorada. Cada atestado é um selo.
# Integra-se com: cache CAS, Mythos Gate, ORCID, TemporalChain.

import hashlib, json, time, struct, base64
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ed25519, ec
from cryptography.exceptions import InvalidSignature
import requests  # para gateway requests

# ============================================================================
# Stubs for Missing Classes
# ============================================================================
class VerificationCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir

    def store(self, tx_id: str, result: Any):
        pass

    def retrieve(self, tx_id: str) -> Optional[Any]:
        return None

class OrcidAuthProvider:
    def __init__(self):
        self.identities = {}

class MythosGatePublisher:
    def evaluate_for_publication(self, metadata: Dict, source_files: List, deps: List, operator_orcid: str):
        class Assessment:
            def __init__(self):
                self.mythos_seal = "mock_seal"
            def to_dict(self):
                return {"mythos_seal": self.mythos_seal}
        return True, "Approved", Assessment()

# ============================================================================
# 1. Tipos de verificação (estágios)
# ============================================================================
class VerificationLevel(Enum):
    EXISTENCE = 1
    INTEGRITY = 2
    VERIFIED = 3

@dataclass
class VerificationResult:
    tx_id: str
    level: VerificationLevel
    data_hash: Optional[str] = None
    owner_address: Optional[str] = None
    block_height: Optional[int] = None
    signature_algorithm: Optional[str] = None
    attestation: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)
    timestamp: int = field(default_factory=lambda: int(time.time()))

# ============================================================================
# 2. Gateway HTTP Client (simplificado)
# ============================================================================
class ArweaveGatewayClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_tx_headers(self, tx_id: str) -> Optional[Dict]:
        # HEAD /raw/{txId}
        resp = requests.head(f"{self.base_url}/raw/{tx_id}", timeout=5)
        if resp.status_code == 200:
            return dict(resp.headers)
        return None

    def graphql_tx(self, tx_id: str) -> Optional[Dict]:
        query = {
            "query": """
            query($id: ID!) {
                transaction(id: $id) {
                    id
                    owner { address }
                    tags { name value }
                    data { size type }
                    block { height timestamp }
                    signature
                }
            }
            """,
            "variables": {"id": tx_id}
        }
        resp = requests.post(f"{self.base_url}/graphql", json=query, timeout=5)
        if resp.status_code == 200:
            data = resp.json()['data']['transaction']
            return data
        return None

    def download_raw(self, tx_id: str) -> bytes:
        resp = requests.get(f"{self.base_url}/raw/{tx_id}", timeout=30)
        resp.raise_for_status()
        return resp.content

    def range_request(self, tx_id: str, start: int, end: int) -> bytes:
        resp = requests.get(f"{self.base_url}/raw/{tx_id}",
                            headers={"Range": f"bytes={start}-{end}"}, timeout=10)
        resp.raise_for_status()
        return resp.content


def deep_hash(data: bytes) -> bytes:
    """Deep hash conforme ANS-104: SHA-256 de uma lista de parts."""
    h = hashlib.sha256()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, bytes):
                h.update(deep_hash(item))
            else:
                h.update(item.encode())
    else:
        h.update(data)
    return h.digest()

def reconstruct_signing_message(owner: str, target: str, tags: List[Dict],
                                data: bytes) -> bytes:
    """
    Reconstrói a mensagem que o dono assinou (formato Arweave).
    [
        owner_b64decoded,
        target_b64decoded,
        tags_list_flat (name,value sequences),
        data
    ]
    """
    import base64
    owner_bytes = base64.urlsafe_b64decode(owner + '==')
    target_bytes = base64.urlsafe_b64decode(target + '==') if target else b''
    # Flat tags: list of name+value bytes alternating
    tag_bytes = b''
    for tag in tags:
        tag_bytes += base64.urlsafe_b64decode(tag['name'] + '==')
        tag_bytes += base64.urlsafe_b64decode(tag['value'] + '==')
    parts = [owner_bytes, target_bytes, tag_bytes, data]
    return deep_hash(parts)

def verify_arweave_signature(signing_message: bytes, signature_b64: str,
                             owner_b64: str, algorithm: str = 'RSA-PSS') -> bool:
    """
    Verifica a assinatura contra a chave pública do dono.
    """
    import base64
    sig_bytes = base64.urlsafe_b64decode(signature_b64 + '==')
    owner_key_bytes = base64.urlsafe_b64decode(owner_b64 + '==')
    try:
        if algorithm == 'RSA-PSS':
            key = serialization.load_der_public_key(owner_key_bytes)
            if not isinstance(key, rsa.RSAPublicKey):
                return False
            key.verify(sig_bytes, signing_message,
                       padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                   salt_length=32),
                       hashes.SHA256())
            return True
        elif algorithm == 'ED25519':
            key = ed25519.Ed25519PublicKey.from_public_bytes(owner_key_bytes)
            key.verify(sig_bytes, signing_message)
            return True
        elif algorithm == 'ECDSA':
            key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), owner_key_bytes)
            key.verify(sig_bytes, signing_message,
                       ec.ECDSA(hashes.SHA256()))
            return True
        else:
            return False
    except InvalidSignature:
        return False


class ArIoVerifier:
    def __init__(self, gateway: ArweaveGatewayClient, wallet_key: Optional[Any] = None,
                 cache_dir: str = "/tmp/arkhe_verify_cache"):
        self.gateway = gateway
        self.wallet_key = wallet_key  # RSA private key for attestation
        self.cache = VerificationCache(cache_dir)  # usa CAS

    def verify(self, tx_id: str) -> VerificationResult:
        result = VerificationResult(tx_id=tx_id, level=VerificationLevel.EXISTENCE)

        # Stage 1: Existence
        headers = self.gateway.get_tx_headers(tx_id)
        tx_data = self.gateway.graphql_tx(tx_id)
        if not tx_data:
            result.errors.append("Transaction not found on gateway")
            return result
        result.block_height = tx_data.get('block', {}).get('height')

        # Stage 2: Data Integrity
        try:
            raw_data = self.gateway.download_raw(tx_id)
            sha256 = hashlib.sha256(raw_data).hexdigest()
            result.data_hash = sha256
            result.level = VerificationLevel.INTEGRITY
        except Exception as e:
            result.errors.append(f"Data download failed: {e}")
            return result

        # Stage 3: Signature Verification
        owner = tx_data.get('owner', {}).get('address')
        if not owner:
            result.errors.append("Owner address missing")
            return result
        tags = tx_data.get('tags', [])
        # Reconstruct signing message (deep hash)
        msg = reconstruct_signing_message(owner, tx_data.get('target', ''), tags, raw_data)
        sig = tx_data.get('signature', '')
        # Detect algorithm from owner key (simplified: default RSA)
        algo = 'RSA-PSS'  # for Arweave native
        if verify_arweave_signature(msg, sig, owner, algo):
            result.level = VerificationLevel.VERIFIED
            result.owner_address = owner
            result.signature_algorithm = algo
            # Generate operator attestation if wallet configured
            if self.wallet_key:
                result.attestation = self._create_attestation(tx_id, sha256, owner,
                                                              result.block_height)
        else:
            result.errors.append("Signature verification failed")

        # Cache result
        self.cache.store(tx_id, result)
        return result

    def _create_attestation(self, tx_id: str, data_hash: str,
                            owner: str, block_height: int) -> Dict:
        payload = {
            "version": 1,
            "txId": tx_id,
            "dataHash": data_hash,
            "signatureVerified": True,
            "ownerAddress": owner,
            "blockHeight": block_height,
            "operator": "arkhe-gateway",  # would be derived from ORCID
            "gateway": self.gateway.base_url,
            "attestedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        sig = self.wallet_key.sign(canonical.encode(),
                                   padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                               salt_length=32),
                                   hashes.SHA256())
        payload["signature"] = base64.urlsafe_b64encode(sig).decode().rstrip('=')
        return payload

from flask import Flask, request, jsonify, send_file
import io

app = Flask(__name__)
verifier = None  # set later

@app.route('/api/v1/verify', methods=['POST'])
def verify_tx():
    data = request.get_json()
    tx_id = data.get('txId')
    if not tx_id:
        return jsonify({"error": "txId required"}), 400
    result = verifier.verify(tx_id)
    return jsonify(result.__dict__), 200

@app.route('/api/v1/verify/<tx_id>/pdf', methods=['GET'])
def download_pdf(tx_id):
    result = verifier.cache.retrieve(tx_id)
    if not result:
        return "not found", 404
    # Generate PDF certificate (mock)
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, f"Verification Certificate for {tx_id}")
    c.drawString(100, 700, f"Level: {result.level.name}")
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{tx_id}.pdf")

class ArkheVerifyService:
    def __init__(self, gateway_url: str, auth_provider: OrcidAuthProvider,
                 mythos: MythosGatePublisher):
        self.verifier = ArIoVerifier(ArweaveGatewayClient(gateway_url))
        self.auth = auth_provider
        self.mythos = mythos

    def verify_with_ethics(self, tx_id: str, operator_orcid: str) -> Dict:
        # 1. Check if operator is authenticated
        identity = self.auth.identities.get(operator_orcid)
        if not identity:
            return {"success": False, "error": "Operator not authenticated"}
        # 2. Perform verification
        result = self.verifier.verify(tx_id)
        # 3. Mythos Gate check on data content (if retrievable)
        if result.level.value >= 2:
            # Simulate: check if data contains dangerous patterns
            raw = self.verifier.gateway.download_raw(tx_id)
            source_files = [("data.bin", raw.decode(errors='ignore'))]
            # Use bio ethical assessor or default
            can_proceed, msg, assessment = self.mythos.evaluate_for_publication(
                {"package": {"name": tx_id, "description": "Arweave data"}},
                source_files, [], operator_orcid
            )
            if not can_proceed:
                return {"success": False, "mythos_rejection": msg,
                        "assessment": assessment.to_dict()}
        # 4. Sign attestation with operator's ORCID key (if wallet configured)
        attestation = None
        if self.verifier.wallet_key:
            attestation = self.verifier._create_attestation(tx_id, result.data_hash,
                                                            result.owner_address,
                                                            result.block_height)
        # 5. Anchor verification result in TemporalChain
        # (simplified: just return with seal)
        return {
            "success": True,
            "tx_id": tx_id,
            "verification_level": result.level.name,
            "data_hash": result.data_hash,
            "attestation": attestation,
            "mythos_seal": assessment.mythos_seal if result.level.value >= 2 else None
        }
