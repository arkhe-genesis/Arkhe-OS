#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_os/_integrity.py
Liturgia criptográfica de verificação de integridade do pacote ARKHE OS.
Fornece selagem, verificação com chave e checagem rápida de conteúdo.
"""

import os
import struct
import hashlib
import hmac
import secrets
import warnings
from pathlib import Path
from typing import Dict, Optional, Tuple

# ============================================================================
# Constantes litúrgicas
# ============================================================================
_MAGIC = struct.pack('!I', 0x41524B48)          # "ARKH"
_DEFAULT_TARGET = "__init__.py"                 # arquivo que representa o pacote
_INTEGRITY_FILE = "_integrity.bin"              # nome do selo
_HASH_ALGO = "sha256"
_HMAC_ALGO = "sha256"
SKIP_INTEGRITY_ENV = "ARKHE_SKIP_INTEGRITY"

# ============================================================================
# Funções internas
# ============================================================================
def _package_root() -> Path:
    """Retorna o diretório onde este módulo está (arkhe_os/)."""
    return Path(__file__).resolve().parent

def _compute_content_hash(file_path: Path, algo: str = _HASH_ALGO) -> str:
    """SHA256 de um arquivo."""
    h = hashlib.new(algo)
    if file_path.is_dir():
        file_path = file_path / _DEFAULT_TARGET
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo alvo não encontrado: {file_path}")
    with open(file_path, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()

def _compute_hash(file_path: Path, algo: str = _HASH_ALGO) -> str:
    return _compute_content_hash(file_path, algo)

def _expected_signature(content_hash: str, key: bytes) -> str:
    """HMAC-SHA256( MAGIC + content_hash ) com a chave fornecida."""
    return hmac.new(key, _MAGIC + content_hash.encode('ascii'), _HMAC_ALGO).hexdigest()

def _read_signature_from_seal(package_root: Path) -> Optional[str]:
    seal_path = package_root / _INTEGRITY_FILE
    if not seal_path.exists():
        return None
    try:
        data = seal_path.read_bytes()
        pos = 4
        hash_len = struct.unpack('!I', data[pos:pos+4])[0]
        pos += 4 + hash_len
        sig_len = struct.unpack('!I', data[pos:pos+4])[0]
        pos += 4
        return data[pos:pos+sig_len].decode('ascii')
    except Exception:
        return None


# ============================================================================
# API pública
# ============================================================================

def generate_integrity_seal(
    package_root: Optional[Path] = None,
    secret_key: Optional[bytes] = None,
    target_file: str = _DEFAULT_TARGET
) -> dict:
    if package_root is None:
        package_root = _package_root()
    res = seal_package(target_file, secret_key, package_root / _INTEGRITY_FILE)
    res["secret_key_hex"] = res["key_hex"]
    return res

def verify_package_integrity(
    package_root: Optional[Path] = None,
    secret_key: Optional[bytes] = None,
    raise_on_failure: bool = False,
    log_level: str = "warning"
) -> Tuple[bool, Optional[str]]:
    if package_root is None:
        package_root = _package_root()

    if os.environ.get(SKIP_INTEGRITY_ENV, "").lower() in ("1", "true", "yes", "on"):
        return True, None

    if secret_key is None:
        env_key = os.environ.get("ARKHE_INTEGRITY_KEY", "")
        if env_key:
            secret_key = bytes.fromhex(env_key)
        else:
            return False, "No secret key provided"

    is_valid = verify_package(secret_key, _DEFAULT_TARGET)
    if is_valid:
        return True, None
    else:
        msg = "Signature verification failed — package may be tampered"
        if raise_on_failure:
            raise IntegrityError(msg)
        return False, msg

class IntegrityError(Exception):
    pass


def seal_package(
    target_file: str = _DEFAULT_TARGET,
    key: Optional[bytes] = None,
    output_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Gera o selo de integridade e retorna um dicionário com os metadados.
    A chave secreta é retornada em 'key_hex' — GUARDE-A COM SEGURANÇA.
    """
    root = _package_root()
    if output_path is None:
        output_path = root / _INTEGRITY_FILE

    if key is None:
        key = secrets.token_bytes(32)
        warnings.warn(
            "Nova chave secreta gerada. Guarde o valor de 'key_hex' em local seguro!",
            RuntimeWarning,
        )

    target = root / target_file
    if not target.exists():
        raise FileNotFoundError(f"Arquivo alvo não encontrado: {target}")

    content_hash = _compute_hash(target)
    signature = _expected_signature(content_hash, key)

    # Escrever o selo binário
    with open(output_path, "wb") as f:
        f.write(_MAGIC)
        f.write(struct.pack('!I', len(content_hash)))
        f.write(content_hash.encode('ascii'))
        f.write(struct.pack('!I', len(signature)))
        f.write(signature.encode('ascii'))

    return {
        "magic": _MAGIC.hex(),
        "content_hash": content_hash,
        "signature": signature,
        "key_hex": key.hex(),
        "integrity_file": str(output_path),
        "verification_hint": f"Set ARKHE_INTEGRITY_KEY={key.hex()} for verification"
    }

def verify_package(key: bytes, target_file: str = _DEFAULT_TARGET) -> bool:
    """
    Verifica a integridade do pacote usando a chave secreta fornecida.
    Retorna True se o conteúdo e a assinatura HMAC estiverem corretos.
    """
    root = _package_root()
    seal_path = root / _INTEGRITY_FILE
    if not seal_path.exists():
        return False

    try:
        data = seal_path.read_bytes()
        magic = data[:4]
        if magic != _MAGIC:
            return False

        pos = 4
        hash_len = struct.unpack('!I', data[pos:pos+4])[0]
        pos += 4
        stored_hash = data[pos:pos+hash_len].decode('ascii')
        pos += hash_len
        sig_len = struct.unpack('!I', data[pos:pos+4])[0]
        pos += 4
        stored_sig = data[pos:pos+sig_len].decode('ascii')

        # Comparar hash do conteúdo atual
        current_hash = _compute_hash(root / target_file)
        if not hmac.compare_digest(current_hash, stored_hash):
            return False

        # Comparar assinatura
        expected_sig = _expected_signature(stored_hash, key)
        return hmac.compare_digest(stored_sig, expected_sig)

    except Exception:
        return False

def check_integrity(verbose: bool = False) -> Dict[str, any]:
    """
    Checagem rápida de integridade (sem chave).
    Verifica apenas se o conteúdo do __init__.py coincide com o hash armazenado.
    """
    root = _package_root()
    seal_path = root / _INTEGRITY_FILE
    result = {
        "valid": False,
        "stored_hash": None,
        "current_hash": None,
        "message": "",
    }

    if not seal_path.exists():
        result["message"] = "Selo de integridade não encontrado."
        if verbose:
            print("❌", result["message"])
        return result

    try:
        data = seal_path.read_bytes()
        if data[:4] != _MAGIC:
            result["message"] = "Magic number inválido."
            if verbose:
                print("❌", result["message"])
            return result

        pos = 4
        hash_len = struct.unpack('!I', data[pos:pos+4])[0]
        pos += 4
        stored_hash = data[pos:pos+hash_len].decode('ascii')

        current_hash = _compute_hash(root / _DEFAULT_TARGET)
        result["stored_hash"] = stored_hash
        result["current_hash"] = current_hash

        if hmac.compare_digest(current_hash, stored_hash):
            result["valid"] = True
            result["message"] = "OK – o conteúdo está íntegro (hash confere)."
            if verbose:
                print("✅", result["message"])
                print(f"   Hash armazenado: {stored_hash[:16]}...")
                print(f"   Hash atual:      {current_hash[:16]}...")
        else:
            result["message"] = "FALHA – o conteúdo foi modificado desde a selagem."
            if verbose:
                print("❌", result["message"])
                print(f"   Hash armazenado: {stored_hash[:16]}...")
                print(f"   Hash atual:      {current_hash[:16]}...")
    except Exception as e:
        result["message"] = f"Erro na leitura do selo: {e}"
        if verbose:
            print("❌", result["message"])

    return result
