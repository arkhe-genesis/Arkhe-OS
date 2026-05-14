import os as _os
import shlex
from . import ArkheSecurityError
from .audit_hooks import auditor

# Destructive commands to block
_DESTRUCTIVE_COMMANDS = ["rm -rf", "mkfs", "dd if=", "wget", "curl"]

def _check_command(command, func_name):
    """Verifica se o comando contém padrões perigosos."""
    if isinstance(command, bytes):
        cmd_str = command.decode('utf-8', errors='ignore')
    elif isinstance(command, str):
        cmd_str = command
    elif isinstance(command, (list, tuple)):
        parts = []
        for a in command:
            if isinstance(a, bytes):
                parts.append(a.decode('utf-8', errors='ignore'))
            else:
                parts.append(str(a))
        cmd_str = " ".join(parts)
    else:
        cmd_str = str(command)

    for dangerous in _DESTRUCTIVE_COMMANDS:
        if dangerous in cmd_str:
            auditor.log_blocked_action(
                function_name=f"os.{func_name}",
                payload=cmd_str,
                severity="critical",
                reason="DESTRUCTIVE_COMMAND"
            )
            raise ArkheSecurityError("Comando bloqueado pelo Guardião Atratora", rule="DESTRUCTIVE_COMMAND")

def system(command):
    _check_command(command, "system")
    return _os.system(command)

def popen(cmd, mode='r', buffering=-1):
    _check_command(cmd, "popen")
    return _os.popen(cmd, mode, buffering)

def execl(file, *args):
    _check_command([file] + list(args), "execl")
    return _os.execl(file, *args)

def execle(file, *args):
    _check_command([file] + list(args), "execle")
    return _os.execle(file, *args)

def execlp(file, *args):
    _check_command([file] + list(args), "execlp")
    return _os.execlp(file, *args)

def execlpe(file, *args):
    _check_command([file] + list(args), "execlpe")
    return _os.execlpe(file, *args)

def execv(path, args):
    _check_command([path] + list(args), "execv")
    return _os.execv(path, args)

def execve(path, args, env):
    _check_command([path] + list(args), "execve")
    return _os.execve(path, args, env)

def execvp(file, args):
    _check_command([file] + list(args), "execvp")
    return _os.execvp(file, args)

def execvpe(file, args, env):
    _check_command([file] + list(args), "execvpe")
    return _os.execvpe(file, args, env)

# Copiar os outros atributos e funções do os module de forma transparente
def __getattr__(name):
    return getattr(_os, name)
