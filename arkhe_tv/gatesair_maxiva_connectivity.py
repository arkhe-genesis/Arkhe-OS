#!/usr/bin/env python3
"""
Substrato 9039 — GatesAir Maxiva Connectivity Script
Estabelece conexão com transmissor GatesAir Maxiva, configura parâmetros
iniciais e habilita monitoramento Φ_C via REST + SNMP.
"""

import asyncio, aiohttp, hashlib, json, time, subprocess, socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

@dataclass
class MaxivaConnectionParams:
    host: str
    rest_port: int = 443
    snmp_port: int = 161
    username: str = "admin"
    password: str = ""
    snmp_community: str = "public"
    snmp_version: str = "v2c"
    use_tls: bool = True

@dataclass
class ConnectivityReport:
    host: str
    rest_api_reachable: bool
    snmp_reachable: bool
    icmp_reachable: bool
    snmp_trap_configured: bool
    syslog_configured: bool
    ldm_capable: bool
    phi_c_baseline: float
    temporal_seal: Optional[str] = None

class GatesAirMaxivaConnectivity:
    """
    Estabelece e valida conectividade completa com GatesAir Maxiva.
    """
    def __init__(self, params: MaxivaConnectionParams, temporal_chain=None):
        self.params = params
        self.temporal = temporal_chain
        self.base_url = f"{'https' if params.use_tls else 'http'}://{params.host}:{params.rest_port}"
        self.session = None

    async def __aenter__(self):
        auth = aiohttp.BasicAuth(self.params.username, self.params.password)
        self.session = aiohttp.ClientSession(auth=auth)
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def full_connectivity_check(self) -> ConnectivityReport:
        """Executa verificação completa de conectividade."""
        report = ConnectivityReport(
            host=self.params.host,
            rest_api_reachable=False,
            snmp_reachable=False,
            icmp_reachable=False,
            snmp_trap_configured=False,
            syslog_configured=False,
            ldm_capable=False,
            phi_c_baseline=0.0,
        )

        # 1. ICMP (ping)
        report.icmp_reachable = self._check_icmp()

        # 2. REST API
        try:
            async with self.session.get(f"{self.base_url}/api/v3/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    report.rest_api_reachable = True
                    report.ldm_capable = data.get("features", {}).get("ldm", False)
        except Exception:
            pass

        # 3. SNMP (simulação)
        report.snmp_reachable = self._check_snmp()

        # 4. SNMP Trap
        report.snmp_trap_configured = await self._configure_snmp_trap()

        # 5. Syslog
        report.syslog_configured = await self._configure_syslog()

        # 6. Φ_C baseline
        report.phi_c_baseline = self._compute_phi_c_baseline(report)

        # 7. Ancorar
        if self.temporal:
            report.temporal_seal = await self.temporal.anchor_event(
                "gatesair_connectivity_established", {
                    "host": self.params.host,
                    "rest_api": report.rest_api_reachable,
                    "snmp": report.snmp_reachable,
                    "phi_c": report.phi_c_baseline,
                    "timestamp": time.time(),
                }
            )

        return report

    def _check_icmp(self) -> bool:
        try:
            subprocess.run(["ping", "-n", "1", "-w", "1000", self.params.host],
                           capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _check_snmp(self) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(b"", (self.params.host, self.params.snmp_port))
            sock.close()
            return True
        except Exception:
            return False

    async def _configure_snmp_trap(self) -> bool:
        trap_config = {
            "trap_destination": f"http://arkhe-gateway:8053/api/snmp/trap",
            "enabled_oids": [
                "1.3.6.1.4.1.3444.1.1.1.1.1.1.0",  # CNR
                "1.3.6.1.4.1.3444.1.1.1.1.1.2.0",  # MER
                "1.3.6.1.4.1.3444.2.1.1.0",         # ARKHE Φ_C anomaly
            ],
        }
        try:
            async with self.session.put(
                f"{self.base_url}/api/v3/snmp/traps", json=trap_config
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def _configure_syslog(self) -> bool:
        try:
            async with self.session.put(
                f"{self.base_url}/api/v3/syslog",
                json={"server": "arkhe-gateway:514", "facility": "local0"}
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _compute_phi_c_baseline(self, report: ConnectivityReport) -> float:
        score = 0.0
        if report.rest_api_reachable: score += 0.3
        if report.snmp_reachable: score += 0.2
        if report.icmp_reachable: score += 0.1
        if report.snmp_trap_configured: score += 0.2
        if report.syslog_configured: score += 0.1
        if report.ldm_capable: score += 0.1
        return round(score, 4)