#!/usr/bin/env python3
"""Configuração de proxies locais para cada rede anônima."""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProxyConfig:
    protocol: str
    proxy_type: str          # socks5h, http, gateway
    host: str = "127.0.0.1"
    port: int = 9050
    control_port: Optional[int] = None
    extra_args: Optional[dict] = None

def get_production_proxies() -> dict:
    """Retorna configuração de proxies para produção."""
    return {
        "tor": ProxyConfig("tor", "socks5h", host="127.0.0.1", port=9050, control_port=9051),
        "i2p": ProxyConfig("i2p", "http", host="127.0.0.1", port=4444),
        "freenet": ProxyConfig("freenet", "gateway", host="127.0.0.1", port=8888),
        "zeronet": ProxyConfig("zeronet", "api", host="127.0.0.1", port=43110)
    }
