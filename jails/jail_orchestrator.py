#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Jail Orchestrator
Canon: ∞.Ω.∇+++.∞.jails.orchestrator
Função: Orquestrar ciclo de vida de jails Arkhe com integração TemporalChain
Linguagem: Python 3.10+ (FreeBSD userspace)
"""

import asyncio
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ArkheJail:
    """Representa uma jail Arkhe configurada."""
    jail_id: str
    name: str
    path: str
    ip4_addr: str
    hostname: str
    memory_limit_mb: int
    cpu_limit_pct: int
    capsicum_enabled: bool
    status: str = "created"  # created, running, stopped, failed
    temporal_seal: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    agent_config: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)

class JailOrchestrator:
    """
    Orchestrator para gestão de jails Arkhe.
    Funcionalidades:
    • Criação via jail_create C wrapper
    • Gestão de ciclo de vida (start/stop/restart)
    • Injeção de configuração de agente
    • Integração com TemporalChain para auditoria
    • Monitoramento de saúde via jls(8)
    """

    JAIL_CREATE_BIN = "/usr/local/sbin/arkhe_jail_create"
    JAIL_BASE_PATH = "/usr/local/jails"
    CONFIG_BASE_PATH = "/usr/local/etc/arkhe/jails"

    def __init__(
        self,
        temporal_chain_client=None,
        phi_bus_client=None,
        base_zfs_dataset: str = "zroot/arkhe/jails"
    ):
        self.temporal = temporal_chain_client
        self.phi_bus = phi_bus_client
        self.base_zfs = base_zfs_dataset
        self._active_jails: Dict[str, ArkheJail] = {}
        self._jail_config_template = """
# ARKHE Jail Configuration
# Generated: {timestamp}
# Canon: ∞.Ω.∇+++.∞.jails.config

name={name}
path={path}
ip4_addr={ip4_addr}
hostname={hostname}
memory_limit_mb={memory_limit_mb}
cpu_limit_pct={cpu_limit_pct}
allow_raw_sockets={allow_raw_sockets}
enable_capsicum={enable_capsicum}
"""

    async def create_jail(
        self,
        name: str,
        ip4_addr: str,
        memory_limit_mb: int = 2048,
        cpu_limit_pct: int = 50,
        capsicum_enabled: bool = True,
        agent_config: Optional[Dict] = None
    ) -> ArkheJail:
        """Cria nova jail Arkhe com configuração segura."""
        # Gerar IDs únicos
        jail_id = hashlib.sha3_256(
            f"{name}:{ip4_addr}:{time.time()}".encode()
        ).hexdigest()[:12]

        jail_path = f"{self.JAIL_BASE_PATH}/{name}"
        hostname = f"arkhe-{name}"

        # Criar diretório da jail se não existir
        Path(jail_path).mkdir(parents=True, exist_ok=True)

        # Gerar arquivo de configuração
        config_path = f"{self.CONFIG_BASE_PATH}/{name}.conf"
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        config_content = self._jail_config_template.format(
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            name=name,
            path=jail_path,
            ip4_addr=ip4_addr,
            hostname=hostname,
            memory_limit_mb=memory_limit_mb,
            cpu_limit_pct=cpu_limit_pct,
            allow_raw_sockets=0,
            enable_capsicum=1 if capsicum_enabled else 0
        )

        with open(config_path, 'w') as f:
            f.write(config_content)

        # Executar jail_create C wrapper
        try:
            result = subprocess.run(
                [self.JAIL_CREATE_BIN, config_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"jail_create failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout creating jail {name}")
            raise

        # Criar objeto ArkheJail
        jail = ArkheJail(
            jail_id=jail_id,
            name=name,
            path=jail_path,
            ip4_addr=ip4_addr,
            hostname=hostname,
            memory_limit_mb=memory_limit_mb,
            cpu_limit_pct=cpu_limit_pct,
            capsicum_enabled=capsicum_enabled,
            agent_config=agent_config
        )

        # Ancorar na TemporalChain
        if self.temporal:
            jail.temporal_seal = await self.temporal.anchor_event(
                "jail_created",
                {
                    "jail_id": jail_id,
                    "name": name,
                    "ip4_addr": ip4_addr,
                    "capsicum_enabled": capsicum_enabled,
                    "memory_limit_mb": memory_limit_mb,
                    "timestamp": time.time()
                }
            )

        self._active_jails[jail_id] = jail
        logger.info(f"✅ Jail criada: {name} ({jail_id})")

        return jail

    async def start_agent_in_jail(
        self,
        jail_id: str,
        agent_binary: str,
        agent_args: List[str]
    ) -> bool:
        """Inicia agente Arkhe dentro de jail com Capsicum se habilitado."""
        jail = self._active_jails.get(jail_id)
        if not jail:
            raise ValueError(f"Jail não encontrada: {jail_id}")

        # Comando para executar dentro da jail
        if jail.capsicum_enabled:
            # Usar entrypoint Capsicum
            cmd = [
                "jexec", jail.name,
                "/usr/local/bin/arkhe_capsicum_entry",
                agent_binary
            ] + agent_args
        else:
            cmd = ["jexec", jail.name, agent_binary] + agent_args

        try:
            # Executar em background
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            jail.status = "running"
            logger.info(f"🚀 Agente iniciado em jail {jail.name}")
            return True

        except Exception as e:
            jail.status = "failed"
            logger.error(f"❌ Falha ao iniciar agente em {jail.name}: {e}")
            return False

    async def stop_jail(self, jail_id: str) -> bool:
        """Para jail e limpa recursos."""
        jail = self._active_jails.get(jail_id)
        if not jail:
            return False

        try:
            # Parar jail via jail(8)
            result = subprocess.run(
                ["jail", "-r", jail.name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                jail.status = "stopped"
                logger.info(f"🛑 Jail parada: {jail.name}")

                # Ancorar na TemporalChain
                if self.temporal:
                    await self.temporal.anchor_event(
                        "jail_stopped",
                        {
                            "jail_id": jail_id,
                            "name": jail.name,
                            "timestamp": time.time()
                        }
                    )
                return True
            else:
                logger.error(f"❌ Falha ao parar jail {jail.name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao parar jail {jail.name}: {e}")
            return False

    def list_active_jails(self) -> List[Dict]:
        """Lista jails ativas com status via jls(8)."""
        try:
            result = subprocess.run(
                ["jls", "-n", "-o", "jid,name,hostname,ip4.addr,path"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            jails = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    jid, name, hostname, ip4_addr, path = parts[:5]
                    # Encontrar jail no nosso registro
                    for jail in self._active_jails.values():
                        if jail.name == name:
                            jails.append({
                                "jid": jid,
                                "jail_id": jail.jail_id,
                                "name": name,
                                "hostname": hostname,
                                "ip4_addr": ip4_addr,
                                "path": path,
                                "status": jail.status,
                                "capsicum": jail.capsicum_enabled
                            })
                            break

            return jails

        except Exception as e:
            logger.error(f"❌ Erro ao listar jails: {e}")
            return []

    def get_orchestration_statistics(self) -> Dict:
        """Retorna estatísticas de orquestração."""
        return {
            "total_jails_created": len(self._active_jails),
            "running_jails": sum(1 for j in self._active_jails.values() if j.status == "running"),
            "capsicum_enabled_count": sum(1 for j in self._active_jails.values() if j.capsicum_enabled),
            "total_memory_allocated_mb": sum(j.memory_limit_mb for j in self._active_jails.values()),
            "jails_by_status": {
                status: sum(1 for j in self._active_jails.values() if j.status == status)
                for status in ["created", "running", "stopped", "failed"]
            }
        }
