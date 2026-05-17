import asyncio
import hashlib
import time
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class InnoSetupTool:
    """
    Inno Setup Tool Canonical Implementation (Substrato 214)
    Handles idempotent compilation, HSM PQC signing, and integration with the Arkhe Tool Calling System.
    """

    def __init__(self, temporal=None, delta_mem=None, hsm_mock=None):
        self.temporal = temporal
        self.delta_mem = delta_mem
        self.build_cache = {}  # In-memory cache for idempotency
        self.hsm = hsm_mock if hsm_mock else self._default_hsm_mock()

    def _default_hsm_mock(self):
        class HSM:
            async def sign(self, data: bytes, key_label: str) -> str:
                return hashlib.sha3_256(data).hexdigest() + "_hsm_signed_dilithium3"
        return HSM()

    async def compile_installer(self, params: Dict[str, Any]=None, **kwargs) -> Dict[str, Any]:
        if params is None:
            params = kwargs
        """
        Compiles an installer using Inno Setup with idempotency.
        """
        script_content = params.get("script_content", "")
        installer_name = params.get("installer_name", "arkhe_setup.exe")
        output_dir = params.get("output_dir", "./build/windows")
        sign_with_hsm = params.get("sign_with_hsm", True)

        # 1. Idempotency: hash do script -> cache lookup
        script_hash = hashlib.sha3_256(script_content.encode()).hexdigest()
        if script_hash in self.build_cache:
            logger.info(f"🔁 Idempotency cache hit for {script_hash}")
            return {
                "installer_path": self.build_cache[script_hash],
                "cache_hit": True,
                "script_hash": script_hash,
                "installer_name": installer_name
            }

        # 2. Mock Compilation: ISCC.exe execution
        start_time = time.time()
        installer_path = os.path.join(output_dir, installer_name)
        os.makedirs(output_dir, exist_ok=True)
        # Mocking creation of the exe
        with open(installer_path, "wb") as f:
            f.write(b"MOCK_EXE_DATA:" + script_content.encode())

        # 3. PQC Signing via HSM
        signature = None
        if sign_with_hsm:
            try:
                with open(installer_path, "rb") as f:
                    file_data = f.read()
                signature = await self.hsm.sign(file_data, key_label="dilithium3")
            except Exception as e:
                logger.warning(f"HSM falhou, fallback para SHA3-256: {e}")
                # Fallback SHA3-256
                signature = hashlib.sha3_256(file_data).hexdigest() + "_classic_fallback"

        latency_ms = (time.time() - start_time) * 1000

        # 4. TemporalChain Anchoring
        if self.temporal:
            if hasattr(self.temporal, "anchor_event"):
                await self.temporal.anchor_event("installer_compiled", {
                    "installer_name": installer_name,
                    "script_hash": script_hash,
                    "signed": bool(signature),
                    "timestamp": time.time(),
                    "latency_ms": latency_ms
                })

        # 4.5. delta_mem write_experience (if available)
        if hasattr(self, "delta_mem") and self.delta_mem:
            features = {
                "script_hash": script_hash,
                "installer_name": installer_name,
                "success": True,
                "latency_ms": latency_ms
            }
            if hasattr(self.delta_mem, "write_experience"):
                if asyncio.iscoroutinefunction(self.delta_mem.write_experience):
                    await self.delta_mem.write_experience("inno_build", features)
                else:
                    self.delta_mem.write_experience("inno_build", features)

        # 5. Update Cache
        self.build_cache[script_hash] = installer_path

        return {
            "installer_path": installer_path,
            "cache_hit": False,
            "script_hash": script_hash,
            "installer_name": installer_name,
            "signature": signature,
            "latency_ms": latency_ms
        }

    async def generate_iss_template(self, params: Dict[str, Any]=None, **kwargs) -> Dict[str, Any]:
        if params is None:
            params = kwargs
        """
        Gera um template .iss com parâmetros canônicos.
        """
        app_name = params.get("app_name", "ARKHE OS")
        version = params.get("version", "1.0.0")
        publisher = params.get("publisher", "Arkhe Network")
        output_dir = params.get("output_dir", "{pf}\\ARKHE OS")
        output_filename = params.get("output_filename", "arkhe_setup")

        template = f"""[Setup]
AppName={app_name}
AppVersion={version}
AppPublisher={publisher}
DefaultDirName={output_dir}
DefaultGroupName={app_name}
OutputBaseFilename={output_filename}
Compression=lzma
SolidCompression=yes

[Files]
Source: "mock_source.exe"; DestDir: "{{app}}"; Flags: ignoreversion
"""
        return {
            "script_content": template,
            "app_name": app_name,
            "version": version
        }
