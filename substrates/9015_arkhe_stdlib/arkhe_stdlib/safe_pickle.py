import pickle as _pickle
import io
from . import ArkheSecurityError
from .audit_hooks import auditor

# Assinaturas de payloads maliciosos conhecidos em pickles
_MALICIOUS_SIGNATURES = [
    b"posix", b"system", b"subprocess", b"Popen", b"__reduce__", b"os\n", b"eval", b"exec"
]

def _check_payload(data):
    """Verifica se o payload serializado contém assinaturas maliciosas."""
    for sig in _MALICIOUS_SIGNATURES:
        if sig in data:
            auditor.log_blocked_action(
                function_name="pickle.loads",
                payload=f"Payload contains unsafe signature: {sig.decode(errors='ignore').strip()}",
                severity="critical",
                reason="UNSAFE_REDUCE_DETECTED"
            )
            raise ArkheSecurityError("Desserialização bloqueada", rule="UNSAFE_REDUCE_DETECTED")

def loads(data, /, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None):
    _check_payload(data)
    return _pickle.loads(data, fix_imports=fix_imports, encoding=encoding, errors=errors, buffers=buffers)

def load(file, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None):
    # Precisamos ler os dados para inspecionar e depois usar BytesIO para o pickle original
    data = file.read()
    _check_payload(data)
    return _pickle.loads(data, fix_imports=fix_imports, encoding=encoding, errors=errors, buffers=buffers)

# Copiar os outros atributos e funções do pickle module de forma transparente
def __getattr__(name):
    return getattr(_pickle, name)
