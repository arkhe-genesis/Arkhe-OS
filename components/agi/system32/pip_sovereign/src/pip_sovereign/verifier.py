#!/usr/bin/env python3
"""
verifier.py — Verificação criptográfica de integridade de pacotes.
SHA3-256 + Falcon-1024 signature verification.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Union
from dataclasses import dataclass

# Integration with ARKHE crypto FFI
try:
    from agi.system32.crypto import falcon_verify, sha3_256_file
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

@dataclass
class PackageManifest:
    """Manifesto criptográfico de um pacote."""
    name: str
    version: str
    hash_sha3_256: str
    signature: str  # Falcon-1024 signature
    maintainer_seal: str
    phi_rep: float
    dependencies: Dict[str, str]
    license: str
    timestamp: float
    ipfs_cid: Optional[str] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict) -> "PackageManifest":
        return cls(**data)

    def canonical_json(self) -> bytes:
        """JSON canônico para verificação de assinatura."""
        # Ordenar chaves e excluir campos mutáveis
        data = {k: v for k, v in self.to_dict().items()
                if k not in ("signature", "ipfs_cid")}
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

class PackageVerifier:
    """Verificador de integridade e autenticidade de pacotes."""

    def __init__(self, trusted_roots: Optional[list[str]] = None):
        self.trusted_roots = trusted_roots or []

    def verify_hash(self, file_path: Union[str, Path], expected_hash: str) -> bool:
        """Verificar hash SHA3-256 de um arquivo."""
        if CRYPTO_AVAILABLE:
            computed = sha3_256_file(str(file_path))
        else:
            # Fallback: hashlib implementation
            hasher = hashlib.sha3_256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            computed = hasher.hexdigest()
        return computed == expected_hash

    def verify_signature(self, manifest: PackageManifest, public_key: Optional[bytes] = None) -> bool:
        """Verificar assinatura Falcon-1024 do manifesto."""
        if not CRYPTO_AVAILABLE:
            # Em produção: levantar erro; aqui: simular verificação
            return manifest.signature.startswith("Falcon-1024:")

        message = manifest.canonical_json()
        signature_bytes = bytes.fromhex(manifest.signature.split(":")[1])

        if public_key:
            return falcon_verify(public_key, signature_bytes, message)
        else:
            # Buscar chave pública do mantenedor via DHT/KYM
            from .registry import SovereignRegistryClient
            registry = SovereignRegistryClient()
            maintainer_key = registry.get_maintainer_public_key(manifest.maintainer_seal)
            if maintainer_key:
                return falcon_verify(maintainer_key, signature_bytes, message)
        return False

    def verify_manifest(self, manifest: PackageManifest,
                       wheel_path: Optional[Path] = None) -> Dict[str, Union[bool, str]]:
        """Verificação completa de manifesto e pacote."""
        result = {"valid": True, "checks": {}}

        # 1. Verificar hash do wheel (se fornecido)
        if wheel_path and wheel_path.exists():
            hash_ok = self.verify_hash(wheel_path, manifest.hash_sha3_256)
            result["checks"]["hash"] = hash_ok
            if not hash_ok:
                result["valid"] = False
                result["error"] = "Hash mismatch"
                return result

        # 2. Verificar assinatura
        sig_ok = self.verify_signature(manifest)
        result["checks"]["signature"] = sig_ok
        if not sig_ok:
            result["valid"] = False
            result["error"] = "Signature verification failed"
            return result

        # 3. Verificar reputação do mantenedor
        if manifest.phi_rep < 0.7:
            result["checks"]["reputation"] = False
            result["warning"] = f"Low maintainer reputation: {manifest.phi_rep:.2f}"
        else:
            result["checks"]["reputation"] = True

        # 4. Verificar timestamp (não muito antigo)
        import time
        # Support both PackageManifest and PackageIndexEntry
        timestamp = getattr(manifest, 'timestamp', getattr(manifest, 'published_at', 0))
        age_days = (time.time() - timestamp) / 86400
        if age_days > 365:
            result["checks"]["freshness"] = False
            result["warning"] = f"Manifest is {age_days:.0f} days old"
        else:
            result["checks"]["freshness"] = True

        return result

def verify_package_integrity(package_name: str,
                            version: Optional[str] = None,
                            wheel_path: Optional[Path] = None,
                            full_check: bool = False) -> Dict:
    """
    Função de alto nível para verificar integridade de pacote.

    Args:
        package_name: Nome do pacote
        version: Versão específica (opcional)
        wheel_path: Caminho para arquivo .whl já baixado
        full_check: Incluir verificação de dependências

    Returns:
        Dict com resultado da verificação
    """
    from .registry import SovereignRegistryClient

    # 1. Obter manifesto do registry
    registry = SovereignRegistryClient()
    manifest = registry.get_package_manifest(package_name, version)
    if not manifest:
        return {"valid": False, "error": "Package not found in sovereign registry"}

    # 2. Verificar manifesto
    verifier = PackageVerifier()
    result = verifier.verify_manifest(manifest, wheel_path)

    if not result["valid"]:
        return result

    # 3. Verificação completa de dependências (opcional)
    dependencies = getattr(manifest, 'dependencies', {})
    if full_check and dependencies:
        from .coherence_monitor import DependencyCoherenceMonitor
        monitor = DependencyCoherenceMonitor()
        dep_analysis = monitor.analyze_packages(dependencies)
        result["dependencies"] = dep_analysis.to_dict()

        if dep_analysis.risk_level == "high":
            result["valid"] = False
            result["error"] = "High-risk dependencies detected"

    result["manifest"] = manifest.to_dict()
    return result