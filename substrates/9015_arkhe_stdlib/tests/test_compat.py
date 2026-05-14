import pytest
import os
import sys
import builtins
import importlib
from arkhe_stdlib import compat

def test_compat_status_disabled():
    if "ARKHE_STDLIB_ENABLED" in os.environ:
        del os.environ["ARKHE_STDLIB_ENABLED"]
    status = compat.status()
    assert "DISABLED" in status

def test_compat_status_enabled():
    os.environ["ARKHE_STDLIB_ENABLED"] = "1"
    status = compat.status()
    assert "PROTECTED" in status
    del os.environ["ARKHE_STDLIB_ENABLED"]

def test_compat_activate():
    os.environ["ARKHE_STDLIB_ENABLED"] = "1"

    # Salvar referências originais
    orig_eval = builtins.eval
    orig_open = builtins.open

    try:
        compat.activate()

        # Verificar se as funções foram substituídas
        assert builtins.eval != orig_eval
        assert builtins.open != orig_open

        # Verificar sys.modules substitution
        assert 'os' in sys.modules

    finally:
        # Restaurar para não quebrar outros testes
        builtins.eval = orig_eval
        builtins.open = orig_open
        del os.environ["ARKHE_STDLIB_ENABLED"]
