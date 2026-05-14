import builtins as _builtins
from . import ArkheSecurityError
from .audit_hooks import auditor
import inspect

_DANGEROUS_BUILTINS = ["__import__", "eval", "exec", "compile", "open"]

_orig_eval = _builtins.eval
_orig_exec = _builtins.exec
_orig_compile = _builtins.compile

def _check_source(source, func_name):
    """Verifica se o código fonte contém chamadas a builtins perigosos."""
    if not isinstance(source, str):
        return

    for dangerous in _DANGEROUS_BUILTINS:
        if dangerous in source:
            auditor.log_blocked_action(
                function_name=func_name,
                payload=source,
                severity="high",
                reason="DANGEROUS_BUILTIN"
            )
            raise ArkheSecurityError(f"{func_name} bloqueado", severity="high", rule="DANGEROUS_BUILTIN")

def safe_eval(source, globals=None, locals=None):
    _check_source(source, "eval")
    # Se omitidos, usar o contexto do chamador, não o nosso (2 frames acima)
    if globals is None:
        caller_frame = inspect.currentframe().f_back
        globals = caller_frame.f_globals
        if locals is None:
            locals = caller_frame.f_locals
    return _orig_eval(source, globals, locals)

def safe_exec(source, globals=None, locals=None):
    _check_source(source, "exec")
    # Se omitidos, usar o contexto do chamador
    if globals is None:
        caller_frame = inspect.currentframe().f_back
        globals = caller_frame.f_globals
        if locals is None:
            locals = caller_frame.f_locals
    return _orig_exec(source, globals, locals)

def safe_compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1, **kwargs):
    # Bypass for pytest internally reading ast
    if isinstance(filename, str) and (filename.endswith('.py') or filename == "source" or 'ast' in filename):
        return _orig_compile(source, filename, mode, flags, dont_inherit, optimize, **kwargs)

    if isinstance(source, (str, bytes)):
        _check_source(source.decode('utf-8') if isinstance(source, bytes) else source, "compile")
    return _orig_compile(source, filename, mode, flags, dont_inherit, optimize, **kwargs)

# Exportando para facilitar a substituição
eval = safe_eval
exec = safe_exec
compile = safe_compile
