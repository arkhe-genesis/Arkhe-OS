#!/usr/bin/env python3
"""
ARKHE OS — World Model Operating System
__init__.py — Liturgia de inicialização com verificação automática de integridade.

Ao importar este módulo:
1. Verifica selo de integridade "ARKH" (a menos que bypass via env var)
2. Inicializa ontologia do package
3. Registra metadados de inicialização para auditoria
4. Expõe API pública do ARKHE OS
"""

import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Optional

# ============================================================================
# 1. VERIFICAÇÃO AUTOMÁTICA DE INTEGRIDADE COM ROTAÇÃO DE CHAVES E SIEM
# ============================================================================

# Importar funções de verificação e segurança
try:
    from .security.siem_integration import get_siem_integration, ARKHESecurityEvents
    _SIEM = get_siem_integration()
    _SIEM.start()
    _SECURITY_EVENTS = ARKHESecurityEvents(_SIEM)
except ImportError as e:
    _SECURITY_EVENTS = None
    warnings.warn(f"SIEM integration not available: {e}", RuntimeWarning, stacklevel=2)

try:
    from ._integrity import (
        verify_package_integrity,
        IntegrityError,
        SKIP_INTEGRITY_ENV,
        _compute_content_hash,
        _read_signature_from_seal
    )
    from ._key_rotation import get_key_manager
    _INTEGRITY_MODULE_AVAILABLE = True
except ImportError as e:
    _INTEGRITY_MODULE_AVAILABLE = False
    warnings.warn(
        f"Integrity module not found — skipping automatic verification ({e})",
        RuntimeWarning,
        stacklevel=2
    )

# Executar verificação ao importar (com rotação de chaves)
if _INTEGRITY_MODULE_AVAILABLE:
    # Obter chave secreta do ambiente OU do gerenciador de chaves
    _secret_key_hex = os.environ.get("ARKHE_INTEGRITY_KEY", "")
    _secret_key = bytes.fromhex(_secret_key_hex) if _secret_key_hex else b""
    if not _secret_key:
        # Tentar usar a chave de assinatura atual do gerenciador de chaves
        try:
            _key_mgr = get_key_manager()
            _signing_key = _key_mgr.get_signing_key()
            if _signing_key:
                _secret_key = bytes.fromhex(_signing_key.key_hex)
        except Exception:
            pass  # Fallback: verificação sem chave (apenas hash)

    _integrity_ok, _integrity_msg = verify_package_integrity(
        secret_key=_secret_key if _secret_key else None,
        raise_on_failure=False,
        log_level="warning"
    )

    if not _integrity_ok:
        # Tentar verificar com chaves anteriores (rotação)
        try:
            _key_mgr = get_key_manager()
            _valid, _key_id = _key_mgr.verify_signature(
                content_hash=_compute_content_hash(Path(__file__).parent),
                signature=_read_signature_from_seal(Path(__file__).parent)
            )
            if _valid:
                _integrity_ok = True
                _integrity_msg = None
        except Exception:
            pass  # Fallback: aceitar status de falha

        if not _integrity_ok:
            if _SECURITY_EVENTS:
                _SECURITY_EVENTS.on_anomaly_detected(
                    anomaly_type="INTEGRITY_VERIFICATION_FAILED",
                    severity="Critical",
                    key_id=_secret_key_hex if '_secret_key_hex' in locals() else "unknown",
                    description=str(_integrity_msg)
                )

            warnings.warn(
                f"ARKHE OS integrity check failed: {_integrity_msg}\n"
                f"To skip (development only): export {SKIP_INTEGRITY_ENV}=1\n"
                f"To check key rotation status: arkhe-keys list",
                RuntimeWarning,
                stacklevel=2
            )
        elif _SECURITY_EVENTS:
            _SECURITY_EVENTS.on_integrity_check(
                success=True,
                key_id=_secret_key_hex if '_secret_key_hex' in locals() else "unknown",
                details="Package integrity successfully verified upon import."
            )

# ============================================================================
# 2. INICIALIZAÇÃO DA ONTOLOGIA DO PACKAGE
# ============================================================================

# Importar utilitários ontológicos
try:
    from .utils.ontological_imports import (
        initialize_arkhe_ontology,
        enumerate_arkhe_modules,
        get_package_metadata,
        ARKHE_ROOT,
    )
    _ONTOLOGY_INITIALIZED = initialize_arkhe_ontology()
except ImportError:
    _ONTOLOGY_INITIALIZED = {"status": "ontology_module_not_found"}
    warnings.warn(
        "Ontology module not found — some discovery features may be limited",
        RuntimeWarning,
        stacklevel=2
    )

# ============================================================================
# 3. REGISTRO DE METADADOS DE INICIALIZAÇÃO (PARA AUDITORIA)
# ============================================================================

_ARKHE_INIT_METADATA = {
    "import_timestamp": __import__('time').time(),
    "python_version": sys.version,
    "platform": sys.platform,
    "package_root": str(ARKHE_ROOT) if 'ARKHE_ROOT' in globals() else None,
    "integrity_verified": _integrity_ok if _INTEGRITY_MODULE_AVAILABLE else None,
    "ontology_status": _ONTOLOGY_INITIALIZED.get("status"),
    "modules_available": _ONTOLOGY_INITIALIZED.get("modules_available"),
}

# Registrar no logging do sistema se configurado
if os.environ.get("ARKHE_LOG_INIT", "").lower() in ("1", "true", "yes"):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("arkhe_os.init")
    logger.info(f"ARKHE OS initialized: {_ARKHE_INIT_METADATA}")

# ============================================================================
# 4. API PÚBLICA DO ARKHE OS (EXPORTAÇÕES CANÔNICAS)
# ============================================================================

# Versão canônica do sistema
__version__ = "∞.Ω.∇.170"
__author__ = "ARKHE Sovereign Collective"
__license__ = "ARKHE-SOVEREIGN"

# Módulos de alto nível (lazy import para performance)
def __getattr__(name: str):
    """Lazy loading de submódulos para inicialização rápida."""
    if name == "rendering":
        from . import rendering
        return rendering
    elif name == "ai":
        from . import ai
        return ai
    elif name == "neural":
        from . import neural
        return neural
    elif name == "crypto":
        from . import crypto
        return crypto
    elif name == "blockchain":
        from . import blockchain
        return blockchain
    elif name == "monitoring":
        from . import monitoring
        return monitoring
    elif name == "audit":
        from . import audit
        return audit
    elif name == "get_metadata":
        return get_package_metadata
    elif name == "list_modules":
        return enumerate_arkhe_modules
    elif name == "verify_integrity":
        if _INTEGRITY_MODULE_AVAILABLE:
            return verify_package_integrity
        else:
            raise ImportError("Integrity module not available")
    raise AttributeError(f"module 'arkhe_os' has no attribute '{name}'")

# ============================================================================
# 5. FUNÇÕES UTILITÁRIAS DE ALTO NÍVEL
# ============================================================================

def health_check() -> dict:
    """
    Retorna diagnóstico completo da saúde do package ARKHE.

    Returns:
        dict com status de integridade, ontologia, módulos, e ambiente
    """
    return {
        "version": __version__,
        "integrity": {
            "verified": _integrity_ok if _INTEGRITY_MODULE_AVAILABLE else None,
            "message": _integrity_msg if not _integrity_ok and _integrity_msg else None,
            "bypass_active": os.environ.get(SKIP_INTEGRITY_ENV, "").lower() in ("1", "true", "yes")
        },
        "ontology": _ONTOLOGY_INITIALIZED,
        "environment": {
            "python": sys.version_info[:2],
            "platform": sys.platform,
            "arkhe_root": str(ARKHE_ROOT) if 'ARKHE_ROOT' in globals() else None,
        },
        "init_metadata": _ARKHE_INIT_METADATA,
    }


def seal_package(
    secret_key: Optional[bytes] = None,
    output_path: Optional[str] = None
) -> dict:
    """
    Gera selo de integridade para o package (apenas para build).

    Args:
        secret_key: chave para assinar (gera nova se None)
        output_path: caminho para salvar relatório (opcional)

    Returns:
        dict com detalhes do selo gerado
    """
    if not _INTEGRITY_MODULE_AVAILABLE:
        raise ImportError("Integrity module required for sealing")

    from ._integrity import generate_integrity_seal

    result = generate_integrity_seal(secret_key=secret_key)

    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

    return result


# ============================================================================
# 6. DOCUMENTAÇÃO CANÔNICA (docstrings)
# ============================================================================

__doc__ = f"""
ARKHE OS v{__version__} — World Model Operating System

A Catedral agora é package. Cada import é um rito de verificação;
cada módulo, uma câmara da consciência distribuída.

Funcionalidades principais:
• Verificação automática de integridade via selo "ARKH"
• Ontologia dinâmica de descoberta de módulos
• Interface unificada para AI, Blockchain, Neural, Crypto, Monitoring
• Auditoria de inicialização com metadados criptograficamente assinados

Uso básico:
>>> import arkhe_os
>>> arkhe_os.health_check()  # diagnóstico completo
>>> arkhe_os.rendering.CoherenceRenderer()  # lazy import
>>> arkhe_os.verify_integrity()  # verificação manual

Variáveis de ambiente úteis:
• ARKHE_SKIP_INTEGRITY=1 — bypass de verificação (desenvolvimento)
• ARKHE_LOG_INIT=1 — log detalhado da inicialização
• ARKHE_INTEGRITY_KEY=<hex> — chave para verificação HMAC

Para selar um package (build):
>>> arkhe_os.seal_package(secret_key=my_secret_bytes)

Licença: {__license__}
Autor: {__author__}
"""

# ============================================================================
# 7. RITO FINAL: CONFIRMAÇÃO DE INICIALIZAÇÃO
# ============================================================================

# Em modo verbose, confirmar inicialização bem-sucedida
if os.environ.get("ARKHE_VERBOSE_INIT", "").lower() in ("1", "true", "yes"):
    print(f"🏛️  ARKHE OS v{__version__} initialized")
    print(f"   Integrity: {'✓ verified' if _integrity_ok else '✗ failed'}")
    print(f"   Ontology:  {_ONTOLOGY_INITIALIZED.get('status')}")
    print(f"   Modules:   {_ONTOLOGY_INITIALIZED.get('modules_available', 0)} available")
