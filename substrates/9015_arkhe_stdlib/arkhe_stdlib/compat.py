import sys
import os
from .audit_hooks import auditor
import builtins
import importlib

def status():
    """Retorna o status do modo de compatibilidade e auditoria."""
    mode = "PROTECTED" if os.environ.get("ARKHE_STDLIB_ENABLED") == "1" else "DISABLED"
    return f"Stdlib Mode: {mode} | Φ_C: {auditor.phi_c} | Blocked: {auditor.blocked_calls} calls"

def activate():
    """Ativa os wrappers de forma transparente, se ativado por variável de ambiente."""
    if os.environ.get("ARKHE_STDLIB_ENABLED") != "1":
        return

    # Substitui builtins perigosos
    from . import safe_eval
    builtins.eval = safe_eval.eval
    builtins.exec = safe_eval.exec
    builtins.compile = safe_eval.compile

    from . import safe_open
    builtins.open = safe_open.open

    # Substituir os métodos diretamente nos módulos reais
    # garante que os módulos que já importaram (ex: import os) recebam os wrappers
    import os as original_os
    from . import safe_os
    original_os.system = safe_os.system
    original_os.popen = safe_os.popen
    original_os.execl = safe_os.execl
    original_os.execle = safe_os.execle
    original_os.execlp = safe_os.execlp
    original_os.execlpe = safe_os.execlpe
    original_os.execv = safe_os.execv
    original_os.execve = safe_os.execve
    original_os.execvp = safe_os.execvp
    original_os.execvpe = safe_os.execvpe

    import pickle as original_pickle
    from . import safe_pickle
    original_pickle.loads = safe_pickle.loads
    original_pickle.load = safe_pickle.load

    import subprocess as original_subprocess
    from . import safe_subprocess
    original_subprocess.run = safe_subprocess.run
    original_subprocess.Popen = safe_subprocess.Popen

    import socket as original_socket
    from . import safe_socket
    original_socket.socket = safe_socket.socket

    # Para interceptar imports futuros também:
    sys.modules['os'] = safe_os
    sys.modules['pickle'] = safe_pickle
    sys.modules['subprocess'] = safe_subprocess
    sys.modules['socket'] = safe_socket
