import builtins as _builtins
import os
from . import ArkheSecurityError
from .audit_hooks import auditor

_orig_open = _builtins.open

# Paths that are blocked from being opened
_UNAUTHORIZED_PATHS = ["/etc/passwd", "/etc/shadow", "/root/.ssh", ".aws/credentials"]

def _check_path(file_path):
    """Verifica se o path do arquivo não é autorizado via MA-S2."""
    if not isinstance(file_path, (str, bytes)):
        return

    path_str = file_path.decode('utf-8') if isinstance(file_path, bytes) else file_path

    # Normalizar o path para evitar evasões como /etc//passwd ou /etc/./passwd
    try:
        norm_path = os.path.normpath(path_str)
    except Exception:
        norm_path = path_str

    for unauthorized in _UNAUTHORIZED_PATHS:
        # Match exato ou match no norm_path (lidando com ../ etc e resolvendo strings de busca)
        if unauthorized in path_str or unauthorized in norm_path:
            auditor.log_blocked_action(
                function_name="open",
                payload=path_str,
                severity="high",
                reason="UNAUTHORIZED_PATH"
            )
            raise ArkheSecurityError(f"Acesso ao arquivo {path_str} bloqueado pelo MA-S2", severity="high", rule="UNAUTHORIZED_PATH")

def safe_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if isinstance(file, (str, bytes, os.PathLike)):
        path_str = os.fspath(file)
        _check_path(path_str)

    return _orig_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

# Exportando para facilitar a substituição
open = safe_open
