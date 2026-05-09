#!/usr/bin/env python3
"""
installer.py — Motor de instalação segura de pacotes Python.
Integra verificação, TEE execution, e registro no ledger.
"""
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union

from .verifier import verify_package_integrity, PackageVerifier
from .registry import SovereignRegistryClient
from .cache import IPFSCache
from .tee_executor import TEEExecutor
from .audit import record_installation

def install_package(package_name: str,
                   version: Optional[str] = None,
                   no_cache: bool = False,
                   dry_run: bool = False,
                   use_tee: bool = False) -> Dict:
    """
    Instalar pacote Python com verificação soberana.

    Returns:
        Dict com status da instalação
    """
    result = {"success": False, "package": package_name, "version": version}

    try:
        # 1. Obter manifesto do registry
        registry = SovereignRegistryClient()
        manifest = registry.get_package_manifest(package_name, version)
        if not manifest:
            result["error"] = "Package not found in sovereign registry"
            return result

        # 2. Verificar integridade
        verification = verify_package_integrity(
            package_name, version, full_check=True
        )
        if not verification["valid"]:
            result["error"] = f"Verification failed: {verification.get('error')}"
            return result

        # 3. Obter wheel do cache IPFS ou baixar
        cache = IPFSCache()
        wheel_path = cache.get(manifest.ipfs_cid) if not no_cache else None

        if not wheel_path:
            wheel_path = _download_wheel(manifest)
            # Adicionar ao cache
            if not no_cache:
                cache.store(manifest.ipfs_cid, wheel_path)

        # 4. Dry run: apenas verificar
        if dry_run:
            result["success"] = True
            result["dry_run"] = True
            result["manifest"] = manifest.to_dict()
            return result

        # 5. Instalar (com ou sem TEE)
        if use_tee:
            executor = TEEExecutor()
            install_result = executor.run_install(wheel_path)
        else:
            install_result = _pip_install_local(wheel_path)

        if not install_result["success"]:
            result["error"] = install_result.get("error", "Installation failed")
            return result

        # 6. Registrar no ledger de auditoria
        record_installation({
            "package": package_name,
            "version": manifest.version,
            "hash": manifest.hash_sha3_256,
            "maintainer": manifest.maintainer_seal,
            "timestamp": manifest.published_at
        })

        result["success"] = True
        result["installed_version"] = manifest.version
        result["hash_verified"] = True
        result["signature_verified"] = True

        return result

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
        return result

def install_requirements(requirements_path: Path,
                        no_cache: bool = False,
                        dry_run: bool = False,
                        use_tee: bool = False) -> int:
    """
    Instalar pacotes de arquivo requirements.txt.

    Returns:
        Número de pacotes que falharam na instalação
    """
    from .coherence_monitor import DependencyCoherenceMonitor

    # 1. Analisar coerência primeiro
    monitor = DependencyCoherenceMonitor()
    analysis = monitor.analyze_requirements(requirements_path)

    if analysis.risk_level == "high" and not dry_run:
        print(f"⚠️  Alto risco de coerência detectado (Φ_C médio: {analysis.avg_coherence:.3f})")
        print("Use --force para ignorar este aviso")
        return len(analysis.low_coherence_packages)

    # 2. Parse requirements
    packages = monitor._parse_requirements(requirements_path)

    # 3. Instalar cada pacote
    failed = 0
    for name, version in packages.items():
        result = install_package(
            package_name=name,
            version=version,
            no_cache=no_cache,
            dry_run=dry_run,
            use_tee=use_tee
        )

        if result["success"]:
            print(f"✅ {name}=={result.get('installed_version', version)}")
        else:
            print(f"❌ {name}: {result.get('error')}")
            failed += 1

    return failed

def _download_wheel(manifest) -> Path:
    """Baixar wheel do IPFS."""
    import requests
    from .config import get_config

    config = get_config()
    gateway = config.get("ipfs_gateway", "http://127.0.0.1:8080")
    url = f"{gateway}/ipfs/{manifest.ipfs_cid}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".whl") as f:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        f.write(resp.content)
        return Path(f.name)

def _pip_install_local(wheel_path: Path) -> Dict:
    """Executar pip install localmente (fallback sem TEE)."""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--no-deps",  # Dependências já verificadas separadamente
            "--force-reinstall",
            str(wheel_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"pip failed: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}