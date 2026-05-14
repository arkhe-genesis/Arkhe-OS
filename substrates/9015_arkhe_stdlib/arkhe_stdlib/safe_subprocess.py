import subprocess as _subprocess
from . import ArkheSecurityError
from .audit_hooks import auditor

# Comandos de subprocesso perigosos para bloquear
_BANNED_COMMANDS = ["rm -rf", "nc", "bash -i", "mkfs"]

def _check_args(args, func_name):
    """Verifica se os argumentos do subprocesso violam a sandbox."""
    if isinstance(args, bytes):
        cmd_str = args.decode('utf-8', errors='ignore')
    elif isinstance(args, str):
        cmd_str = args
    elif isinstance(args, (list, tuple)):
        # Decode components if they are bytes before joining
        parts = []
        for a in args:
            if isinstance(a, bytes):
                parts.append(a.decode('utf-8', errors='ignore'))
            else:
                parts.append(str(a))
        cmd_str = " ".join(parts)
    else:
        cmd_str = str(args)

    for banned in _BANNED_COMMANDS:
        if banned in cmd_str:
            auditor.log_blocked_action(
                function_name=f"subprocess.{func_name}",
                payload=cmd_str,
                severity="critical",
                reason="SANDBOX_VIOLATION"
            )
            raise ArkheSecurityError("Sandbox violation: Process blocked", rule="SANDBOX_VIOLATION")

def run(*popenargs, **kwargs):
    if popenargs:
        _check_args(popenargs[0], "run")
    elif "args" in kwargs:
        _check_args(kwargs["args"], "run")
    return _subprocess.run(*popenargs, **kwargs)

class Popen(_subprocess.Popen):
    def __init__(self, args, **kwargs):
        _check_args(args, "Popen")
        super().__init__(args, **kwargs)

# Copiar os outros atributos e funções do subprocess module de forma transparente
def __getattr__(name):
    return getattr(_subprocess, name)
