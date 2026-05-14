#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utils.py — Utilitários para integração Arkhe-IPython
"""

import os
import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from functools import lru_cache

logger = logging.getLogger(__name__)

class SafeCoreConnection:
    """Gerencia conexão com o Safe Core da Arkhe."""

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("ARKHE_SAFE_CORE_ENDPOINT", "http://localhost:8051")
        self.api_key = api_key or os.getenv("ARKHE_API_KEY")
        self._session = None
        self._cache_dir = Path.home() / ".arkhe" / "ipython_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def session(self):
        """Lazy initialization da sessão HTTP."""
        if self._session is None:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            self._session = requests.Session()

            # Configurar retry com backoff exponencial
            retry = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

            if self.api_key:
                self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

        return self._session

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Chama ferramenta do Safe Core via API MCP."""
        url = f"{self.endpoint}/tools/{tool_name}"
        payload = {"arguments": arguments}

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao chamar ferramenta {tool_name}: {e}")
            return {"error": str(e), "tool": tool_name}

    async def query_audit(self, seal: str) -> Optional[Dict]:
        """Consulta registro de auditoria por selo temporal."""
        url = f"{self.endpoint}/audit/{seal}"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"Erro ao consultar auditoria {seal}: {e}")
            return None

    def cache_result(self, key: str, result: Any, ttl_seconds: int = 300) -> str:
        """Armazena resultado em cache local com TTL."""
        cache_path = self._cache_dir / f"{hashlib.sha3_256(key.encode()).hexdigest()[:16]}.json"

        cache_entry = {
            "result": result,
            "cached_at": time.time(),
            "ttl_seconds": ttl_seconds,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_entry, f, default=str)

        return str(cache_path)

    def get_cached_result(self, key: str) -> Optional[Any]:
        """Recupera resultado do cache se ainda válido."""
        cache_path = self._cache_dir / f"{hashlib.sha3_256(key.encode()).hexdigest()[:16]}.json"

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                entry = json.load(f)

            # Verificar TTL
            if time.time() - entry["cached_at"] > entry["ttl_seconds"]:
                cache_path.unlink()  # Remover cache expirado
                return None

            return entry["result"]
        except Exception:
            return None

    def compute_execution_seal(self, code: str, metadata: Dict) -> str:
        """Computa selo SHA3-256 para ancoragem temporal de execução."""
        seal_data = {
            "code_hash": hashlib.sha3_256(code.encode()).hexdigest(),
            "metadata": metadata,
            "timestamp": time.time(),
            "kernel_id": os.getenv("JPY_SESSION_NAME", "unknown"),
        }
        return hashlib.sha3_256(
            json.dumps(seal_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]


@lru_cache(maxsize=128)
def format_phi_c_display(phi_c: float) -> str:
    """Formata valor de Φ_C para exibição com indicador visual."""
    if phi_c >= 0.99:
        return f"🟢 {phi_c:.4f}"
    elif phi_c >= 0.95:
        return f"🟡 {phi_c:.4f}"
    elif phi_c >= 0.90:
        return f"🟠 {phi_c:.4f}"
    else:
        return f"🔴 {phi_c:.4f}"


def safe_repr(obj: Any, max_length: int = 200) -> str:
    """Representação segura de objeto para logging, com truncamento."""
    repr_str = repr(obj)
    if len(repr_str) > max_length:
        return repr_str[:max_length] + f"... ({len(repr_str) - max_length} chars omitted)"
    return repr_str


def extract_code_context(code: str, context_lines: int = 5) -> Dict[str, Any]:
    """Extrai metadados do código para auditoria."""
    lines = code.split("\n")
    return {
        "line_count": len(lines),
        "char_count": len(code),
        "imports": [line.strip() for line in lines if line.strip().startswith("import ") or line.strip().startswith("from ")],
        "function_defs": [line.strip() for line in lines if line.strip().startswith("def ")],
        "class_defs": [line.strip() for line in lines if line.strip().startswith("class ")],
        "first_n_lines": "\n".join(lines[:context_lines]),
    }
