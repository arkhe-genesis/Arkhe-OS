#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Python Seccomp Wrapper
Integração Python para filtro seccomp nativo via ctypes.
"""

import ctypes
import logging
from pathlib import Path
from typing import Optional
from enum import IntEnum

logger = logging.getLogger(__name__)

class SeccompProfile(IntEnum):
    """Perfis de seccomp disponíveis."""
    STRICT = 0      # Apenas syscalls essenciais
    MODERATE = 1    # Syscalls para execução Python
    PERMISSIVE = 2  # Syscalls para desenvolvimento

class NativeSeccompFilter:
    """
    Wrapper Python para filtro seccomp nativo via libseccomp.

    Uso:
    >>> seccomp = NativeSeccompFilter(lib_path="/usr/lib/libseccomp_filter.so")
    >>> seccomp.apply(SeccompProfile.MODERATE)
    """

    def __init__(self, lib_path: str = "/usr/lib/libseccomp_filter.so"):
        self.lib_path = Path(lib_path)
        self._lib: Optional[ctypes.CDLL] = None
        self._applied = False

        if not self.lib_path.exists():
            logger.warning(f"⚠️  Biblioteca seccomp não encontrada: {lib_path}")
            return

        try:
            self._lib = ctypes.CDLL(str(self.lib_path))
            # Definir assinaturas de funções
            self._lib.py_apply_seccomp.argtypes = [ctypes.c_int]
            self._lib.py_apply_seccomp.restype = ctypes.c_int
            self._lib.list_allowed_syscalls.argtypes = [
                ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t
            ]
            self._lib.list_allowed_syscalls.restype = ctypes.c_int
            logger.info(f"✅ Biblioteca seccomp carregada: {lib_path}")
        except Exception as e:
            logger.error(f"❌ Falha ao carregar biblioteca seccomp: {e}")

    def apply(self, profile: SeccompProfile) -> bool:
        """Aplica filtro seccomp ao processo atual."""
        if not self._lib:
            logger.error("❌ Biblioteca seccomp não disponível")
            return False

        if self._applied:
            logger.warning("⚠️  Filtro seccomp já aplicado")
            return True

        result = self._lib.py_apply_seccomp(int(profile))
        if result == 0:
            self._applied = True
            logger.info(f"✅ Filtro seccomp aplicado: {profile.name}")
            return True
        else:
            logger.error(f"❌ Falha ao aplicar filtro seccomp: código {result}")
            return False

    def get_allowed_syscalls(self, profile: SeccompProfile) -> list[int]:
        """Retorna lista de syscalls permitidos para um perfil."""
        if not self._lib:
            return []

        buffer_size = 4096
        buffer = ctypes.create_string_buffer(buffer_size)

        result = self._lib.list_allowed_syscalls(
            int(profile), buffer, buffer_size
        )
        if result != 0:
            return []

        # Parsear lista de inteiros separados por vírgula
        syscalls_str = buffer.value.decode('utf-8')
        return [int(s) for s in syscalls_str.split(',') if s.strip()]

    def is_applied(self) -> bool:
        """Verifica se filtro seccomp foi aplicado."""
        return self._applied
