import socket as _socket
from . import ArkheSecurityError
from .audit_hooks import auditor

# IP e Portas bloqueadas
_BANNED_PORTS = [22, 23, 3389] # SSH, Telnet, RDP
_BANNED_IPS = ["10.0.0.1", "192.168.0.1"] # Exemplos de IPs locais a bloquear

def _check_address(address, func_name):
    """Monitora tráfego e funciona como firewall de conexões."""
    if not isinstance(address, tuple) or len(address) < 2:
        return

    ip, port = address[0], address[1]

    # Validação simples
    if port in _BANNED_PORTS or ip in _BANNED_IPS:
        auditor.log_blocked_action(
            function_name=f"socket.{func_name}",
            payload=f"{ip}:{port}",
            severity="medium",
            reason="FIREWALL_BLOCKED"
        )
        raise ArkheSecurityError(f"Conexão para {ip}:{port} bloqueada pelo firewall", severity="medium", rule="FIREWALL_BLOCKED")

class socket(_socket.socket):
    """Subclasse de socket que implementa o firewall."""
    def connect(self, address):
        _check_address(address, "connect")
        super().connect(address)

    def connect_ex(self, address):
        _check_address(address, "connect_ex")
        return super().connect_ex(address)

    def bind(self, address):
        _check_address(address, "bind")
        super().bind(address)

# Copiar os outros atributos e funções do socket module de forma transparente
def __getattr__(name):
    return getattr(_socket, name)
