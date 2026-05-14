"""
Arkhe-stdlib v1.0.0 (Substrato 9015)
Integração do Safe Core da Arkhe na biblioteca padrão Python. Wrappers seguros para funções perigosas, hooks de auditoria com ancoragem na TemporalChain, e modo de compatibilidade para substituição transparente da stdlib original.
"""

__version__ = "1.0.0"
__substrate__ = "9015"

class ArkheSecurityError(Exception):
    """Exceção levantada quando uma ação é bloqueada pelo Guardião Atratora / MA-S2."""
    def __init__(self, message, severity="critical", rule="UNKNOWN"):
        super().__init__(f"ArkheSecurityError: {message} [severity: {severity}, rule: {rule}]")
        self.severity = severity
        self.rule = rule
