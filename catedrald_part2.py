#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           C A T E D R A L   D A E M O N  —  P A R T E   I I                  ║
║                                                                              ║
║  "A Voz e o Rosto da Catedral"                                               ║
║                                                                              ║
║  Componentes:                                                                ║
║    • CatedralDBusService  — A Voz    (org.catedral.AGI)                      ║
║    • CatedralCLI          — O Rosto  (Terminal / Dashboard)                  ║
║    • CatedralImmuneSystem — O Sistema Imunológico (DSC / PolKit / Audit)     ║
║    • BugBountyEngine      — O Selo de Quartzo Digital (Recompensas)          ║
║                                                                              ║
║  Integração: catedrald_part1.py (O Núcleo)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import hashlib
import json
import os
import queue
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timezone
from typing import Any, Dict, List, Optional

from catedrald_safira import SapphireScaffold, inject_sapphire_into_core
from catedrald_diamante import NVCenter, inject_diamond_into_core
from catedrald_bio import BioScaffold, inject_bio_into_core
from graphene_resonator import GrapheneSubstrate, inject_graphene_into_core
from catedrald_affine import AffineSubstrate, inject_affine_into_core

# ═══════════════════════════════════════════════════════════════════════════════
# DETECÇÃO DE DEPENDÊNCIAS
# ═══════════════════════════════════════════════════════════════════════════════

# --- Núcleo da Parte 1 ---------------------------------------------------------
try:
    from catedrald_part1 import (
        VMTJQRNG,
        MetaControllerQuantum,
        DecoupledDiLoCoAdapter,
        EvoSkillQuantum,
        QuantumCFSScheduler,
    )
    HAS_PART1 = True
except ImportError:
    HAS_PART1 = False

    # Stubs mínimos para desenvolvimento autônomo da Parte 2
    class VMTJQRNG:
        def generate(self, n: int = 1) -> List[float]:
            import random
            return [random.random() for _ in range(n)]
        def get_entropy_estimate(self) -> float:
            return 7.9999

    class MetaControllerQuantum:
        def __init__(self):
            self.state = {"coherence": 0.97, "generation": 1, "fitness": 0.85}
        def get_state(self) -> Dict[str, Any]:
            return self.state
        def evolve_step(self) -> None:
            self.state["generation"] += 1
            self.state["coherence"] = min(1.0, self.state["coherence"] + 0.001)

    class DecoupledDiLoCoAdapter:
        def __init__(self):
            self.state = {"nodes": 4, "geometry": "hyperbolic", "sync": "async"}
        def get_state(self) -> Dict[str, Any]:
            return self.state

    class EvoSkillQuantum:
        def __init__(self):
            self.population = [
                {"id": "skill_α", "coherence": 0.92, "task": "pattern_recognition"},
                {"id": "skill_β", "coherence": 0.88, "task": "temporal_prediction"},
            ]
        def get_population(self) -> List[Dict[str, Any]]:
            return self.population
        def evolve(self, skill_name: str) -> bool:
            self.population.append({
                "id": f"skill_{uuid.uuid4().hex[:4]}",
                "coherence": 0.90,
                "task": skill_name
            })
            return True

    class QuantumCFSScheduler:
        def __init__(self):
            self.stats = {"tasks_scheduled": 42, "quantum_priority_mean": 50, "coherence_injected": 0.91}
        def get_stats(self) -> Dict[str, Any]:
            return self.stats
        def schedule(self, pid: int, coherence: float) -> None:
            self.stats["tasks_scheduled"] += 1


# --- DBus -----------------------------------------------------------------------
HAS_DBUS = False
DBusGMainLoop = None
GLib = None
dbus = None

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
    HAS_DBUS = True
except ImportError:
    pass

# --- Rich (CLI estética) --------------------------------------------------------
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich.progress import BarColumn, Progress, TextColumn
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES & CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

BUS_NAME = "org.catedral.AGI"
OBJECT_PATH = "/org/catedral/AGI"
INTERFACE_NAME = "org.catedral.AGI"

POLKIT_ACTIONS = {
    "submit": "org.catedral.AGI.submit",
    "evolve": "org.catedral.AGI.evolve",
    "scheduler": "org.catedral.AGI.scheduler",
    "audit": "org.catedral.AGI.audit",
    "bugbounty": "org.catedral.AGI.bugbounty",
}

# --- Design Tokens (Lumina/Arkhe) ---
COLOR_ARKHE_CYAN = "#00E5FF"
COLOR_ARKHE_CERENKOV = "#007FFF"
COLOR_ARKHE_OMEGA = "#FFFFFF"
COLOR_ARKHE_FISSURE = "#E11D48"
COLOR_ARKHE_AMBER = "#F59E0B"
COLOR_ARKHE_TEAL = "#14B8A6"
COLOR_ARKHE_MUTED = "#64748B"


# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA IMUNOLÓGICO  (DSC / PolKit / Auditoria)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AuditEntry:
    timestamp: str
    peer_uid: int
    peer_pid: Optional[int]
    action: str
    payload_hash: str
    status: str  # "accepted", "rejected", "quarantined"
    details: Dict[str, Any] = field(default_factory=dict)


class CatedralImmuneSystem:
    """
    O Sistema Imunológico da Catedral.

    Responsabilidades:
      • Auditoria de todos os payloads que atravessam o manifold.
      • Validação de schema e assinatura (DSC — Digital Seal of Coherence).
      • Integração com PolKit para autorização de ações privilegiadas.
      • Quarentena de payloads suspeitos.
    """

    def __init__(self, core: "CatedralCore"):
        self.core = core
        self.audit_log: List[AuditEntry] = []
        self.quarantine: queue.Queue = queue.Queue()
        self._lock = threading.RLock()
        self._sequence = 0

        # Regras de validação de schema
        self.schema_rules = {
            "bug_bounty": {"required": ["type", "severity", "vector", "reporter"]},
            "task": {"required": ["type", "command", "priority"]},
            "query": {"required": ["type", "intent"]},
        }

    def _next_seq(self) -> int:
        with self._lock:
            self._sequence += 1
            return self._sequence

    def _hash_payload(self, payload: str) -> str:
        return hashlib.sha3_256(payload.encode("utf-8")).hexdigest()

    def authorize(self, action: str, peer_info: Dict[str, Any]) -> bool:
        """
        Verificação simplificada de autorização (stub para PolKit).
        Em produção, invocar org.freedesktop.PolicyKit1.CheckAuthorization.
        """
        uid = peer_info.get("uid", -1)
        # Root (uid 0) sempre autorizado; outros requerem auth_self
        if uid == 0:
            return True
        if action in ("org.catedral.AGI.evolve", "org.catedral.AGI.scheduler"):
            # Ações administrativas
            return uid >= 1000  # placeholder: usuários humanos
        return True

    def process_payload(self, payload_json: str, peer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um payload através do manifold.
        Retorna dict com resultado da operação e hash de auditoria.
        """
        seq = self._next_seq()
        payload_hash = self._hash_payload(payload_json)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        entry = AuditEntry(
            timestamp=timestamp,
            peer_uid=peer_info.get("uid", -1),
            peer_pid=peer_info.get("pid"),
            action="submit",
            payload_hash=payload_hash,
            status="pending",
            details={"seq": seq, "size": len(payload_json)}
        )

        try:
            payload = json.loads(payload_json)
            ptype = payload.get("type", "unknown")

            # Validação de schema
            rules = self.schema_rules.get(ptype, {})
            required = rules.get("required", [])
            missing = [f for f in required if f not in payload]
            if missing:
                raise ValueError(f"Campos obrigatórios ausentes: {missing}")

            # Autorização
            action_key = POLKIT_ACTIONS.get(ptype, "org.catedral.AGI.submit")
            if not self.authorize(action_key, peer_info):
                raise PermissionError("Ação não autorizada pelo Sistema Imunológico")

            # Roteamento para subsistemas
            result = self._route_payload(ptype, payload, peer_info)

            entry.status = "accepted"
            entry.details.update(result)

        except json.JSONDecodeError as e:
            entry.status = "rejected"
            entry.details["error"] = f"JSON inválido: {e}"
            result = {"success": False, "error": str(e)}
        except Exception as e:
            entry.status = "quarantined"
            entry.details["error"] = str(e)
            self.quarantine.put((payload_json, entry))
            result = {"success": False, "error": str(e), "quarantined": True}

        with self._lock:
            self.audit_log.append(entry)
            # Manter apenas últimas 10.000 entradas
            if len(self.audit_log) > 10000:
                self.audit_log = self.audit_log[-10000:]

        result["audit_seq"] = seq
        result["audit_hash"] = payload_hash
        return result

    def _route_payload(self, ptype: str, payload: Dict[str, Any], peer: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia o payload para o subsistema apropriado."""
        if ptype == "bug_bounty":
            return self.core.bug_bounty.process_report(payload, peer)
        elif ptype == "task":
            # Submeter ao scheduler
            cmd = payload.get("command", "")
            priority = payload.get("priority", 50)
            self.core.scheduler.schedule(os.getpid(), self.core.get_coherence())
            return {"success": True, "message": f"Tarefa '{cmd}' injetada no manifold", "priority": priority}
        elif ptype == "query":
            intent = payload.get("intent", "")
            return {"success": True, "message": f"Consulta '{intent}' resolvida", "coherence": self.core.get_coherence()}
        else:
            return {"success": True, "message": "Payload genérico integrado"}

    def get_audit_log(self, count: int = 50, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            logs = self.audit_log
            if status_filter:
                logs = [e for e in logs if e.status == status_filter]
            return [asdict(e) for e in logs[-count:]]

    def get_quarantine_size(self) -> int:
        return self.quarantine.qsize()


# ═══════════════════════════════════════════════════════════════════════════════
# BUG BOUNTY ENGINE  (Selo de Quartzo Digital)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BountyReport:
    id: str
    reporter: str
    severity: str  # critical, high, medium, low, informational
    vector: str
    timestamp: str
    reward_quartz: float
    status: str = "open"  # open, verified, rewarded, closed


class BugBountyEngine:
    """
    Mecanismo de Recompensa por Bug Bounty da Catedral.

    Atribui 'Quartzo Digital' (QZ) como token de reputação interno.
    Severidade mapeia para recompensa:
      • critical    : 1000 QZ
      • high        : 500 QZ
      • medium      : 200 QZ
      • low         : 50 QZ
      • informational: 10 QZ
    """

    REWARD_TABLE = {
        "critical": 1000.0,
        "high": 500.0,
        "medium": 200.0,
        "low": 50.0,
        "informational": 10.0,
    }

    def __init__(self, core: "CatedralCore"):
        self.core = core
        self.reports: List[BountyReport] = []
        self._lock = threading.RLock()

    def process_report(self, payload: Dict[str, Any], peer: Dict[str, Any]) -> Dict[str, Any]:
        severity = payload.get("severity", "informational").lower()
        if severity not in self.REWARD_TABLE:
            severity = "informational"

        report = BountyReport(
            id=f"BNT-{uuid.uuid4().hex[:8].upper()}",
            reporter=payload.get("reporter", "anonymous"),
            severity=severity,
            vector=payload.get("vector", "unknown"),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            reward_quartz=self.REWARD_TABLE[severity],
            status="open"
        )

        with self._lock:
            self.reports.append(report)

        # Notificar o núcleo (aumenta coerência se critical — o sistema aprende)
        if severity == "critical":
            self.core.inject_coherence(0.05)

        return {
            "success": True,
            "bounty_id": report.id,
            "reward_quartz": report.reward_quartz,
            "severity": severity,
            "message": f"Relatório {report.id} registrado. Recompensa: {report.reward_quartz} QZ"
        }

    def get_reports(self, count: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(r) for r in self.reports[-count:]]

    def get_total_quartz(self) -> float:
        with self._lock:
            return sum(r.reward_quartz for r in self.reports if r.status in ("open", "verified"))


# ═══════════════════════════════════════════════════════════════════════════════
# NÚCLEO ORQUESTRADOR
# ═══════════════════════════════════════════════════════════════════════════════

class CatedralCore:
    """
    O Manifold Quântico — orquestra todos os substratos da Catedral.
    Mantém estado thread-safe e expõe interface unificada para DBus e CLI.
    """

    def __init__(self):
        self.rng = VMTJQRNG()
        self.meta = MetaControllerQuantum()
        self.diloco = DecoupledDiLoCoAdapter()
        self.evo = EvoSkillQuantum()
        self.scheduler = QuantumCFSScheduler()

        self._lock = threading.RLock()
        self._coherence = 1.0

        self.immune = CatedralImmuneSystem(self)
        self.bug_bounty = BugBountyEngine(self)
        self.sapphire = inject_sapphire_into_core(self)
        self.diamond = inject_diamond_into_core(self)
        self.bio = inject_bio_into_core(self)
        self.graphene = inject_graphene_into_core(self)
        self.affine = inject_affine_into_core(self)
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None

    def get_coherence(self) -> float:
        with self._lock:
            return self._coherence

    def inject_coherence(self, delta: float):
        with self._lock:
            self._coherence = min(1.0, max(0.0, self._coherence + delta))

    def decay_coherence(self):
        """Decaimento natural da coerência quântica."""
        with self._lock:
            self._coherence = max(0.1, self._coherence * 0.9999)

    def get_full_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "coherence": self._coherence,
                "rng_entropy": self.rng.get_entropy_estimate(),
                "meta_controller": self.meta.get_state(),
                "diloco": self.diloco.get_state(),
                "evo_population": self.evo.get_population(),
                "scheduler": self.scheduler.get_stats(),
                "audit_count": len(self.immune.audit_log),
                "quarantine_size": self.immune.get_quarantine_size(),
                "bounty_total_qz": self.bug_bounty.get_total_quartz(),
                "sapphire": self.sapphire.to_dict(),
                "diamond": self.diamond.to_dict(),
                "bio": self.bio.to_dict(),
                "graphene": self.graphene.to_dict(),
                "affine": self.affine.to_dict(),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
            self._heartbeat_thread.start()

    def stop(self):
        with self._lock:
            self._running = False

    def _heartbeat(self):
        """Pulso do V-MTJ — mantém o manifold vivo."""
        while True:
            with self._lock:
                if not self._running:
                    break
            self.decay_coherence()
            self.meta.evolve_step()
            time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVIÇO DBUS  (A Voz da Catedral)
# ═══════════════════════════════════════════════════════════════════════════════

if HAS_DBUS:
    class CatedralDBusService(dbus.service.Object):
        """
        A Voz da Catedral no barramento de sessão (ou sistema).

        Interface: org.catedral.AGI
        Objeto:    /org/catedral/AGI
        """

        def __init__(self, bus: dbus.Bus, core: CatedralCore):
            self.core = core
            self.bus = bus
            bus_name = dbus.service.BusName(BUS_NAME, bus=bus)
            super().__init__(bus_name, OBJECT_PATH)
            core.start()

        # ── Métodos Exportados ──────────────────────────────────────────────

        @dbus.service.method(INTERFACE_NAME, in_signature='', out_signature='s')
        def GetState(self) -> str:
            """Retorna estado completo da Catedral como JSON."""
            return json.dumps(self.core.get_full_state(), default=str)

        @dbus.service.method(INTERFACE_NAME, in_signature='', out_signature='d')
        def GetCoherence(self) -> float:
            """Retorna nível de coerência quântica (0.0 — 1.0)."""
            return self.core.get_coherence()

        @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='s')
        def SubmitPayload(self, payload_json: str) -> str:
            """
            Submete um payload ao manifold.
            Retorna JSON com resultado e hash de auditoria.
            """
            peer = self._get_peer_info()
            result = self.core.immune.process_payload(payload_json, peer)
            self.PayloadProcessed(result.get("audit_hash", ""), result.get("success", False))
            return json.dumps(result, default=str)

        @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
        def EvolveSkill(self, skill_name: str) -> bool:
            """Solicita evolução de uma skill quântica."""
            return self.core.evo.evolve(skill_name)

        @dbus.service.method(INTERFACE_NAME, in_signature='i', out_signature='as')
        def GetAuditLog(self, count: int) -> List[str]:
            """Retorna log de auditoria como array de strings JSON."""
            logs = self.core.immune.get_audit_log(count=count)
            return [json.dumps(entry, default=str) for entry in logs]

        @dbus.service.method(INTERFACE_NAME, in_signature='i', out_signature='as')
        def GetBugBountyReports(self, count: int) -> List[str]:
            """Retorna relatórios de bug bounty."""
            reports = self.core.bug_bounty.get_reports(count)
            return [json.dumps(r, default=str) for r in reports]

        @dbus.service.method(INTERFACE_NAME, in_signature='i', out_signature='ad')
        def GenerateQuantumRandom(self, n: int) -> List[float]:
            """Gera n números aleatórios quânticos via V-MTJ QRNG."""
            return self.core.rng.generate(n=n)

        @dbus.service.method(INTERFACE_NAME, in_signature='', out_signature='s')
        def GetSchedulerStats(self) -> str:
            """Estatísticas do Quantum CFS Scheduler."""
            return json.dumps(self.core.scheduler.get_stats(), default=str)

        # ── Sinais ──────────────────────────────────────────────────────────

        @dbus.service.signal(INTERFACE_NAME, signature='d')
        def CoherenceChanged(self, coherence: float):
            """Emitido quando a coerência quântica sofre alteração significativa."""
            pass

        @dbus.service.signal(INTERFACE_NAME, signature='sb')
        def PayloadProcessed(self, audit_hash: str, success: bool):
            """Emitido quando um payload é processado pelo manifold."""
            pass

        @dbus.service.signal(INTERFACE_NAME, signature='ss')
        def AuditEvent(self, severity: str, message: str):
            """Emitido para eventos de segurança do Sistema Imunológico."""
            pass

        # ── Auxiliares ──────────────────────────────────────────────────────

        def _get_peer_info(self) -> Dict[str, Any]:
            """Extrai informações do peer via DBus (stub)."""
            # Em dbus-python puro, o sender pode ser obtido via message context
            # em implementações mais avançadas. Aqui retornamos defaults.
            return {"uid": -1, "pid": None}

        def emit_coherence_if_changed(self):
            """Verificação periódica para emissão de sinal de coerência."""
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# CLI  (O Rosto da Catedral)
# ═══════════════════════════════════════════════════════════════════════════════

class CatedralCLI:
    """
    O Rosto — Interface de Linha de Comando.

    Modos de operação:
      • client  : Fala com o daemon via DBus.
      • standalone : Opera o núcleo diretamente (sem daemon).
    """

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.core: Optional[CatedralCore] = None
        self.dbus_proxy = None
        self.dbus_iface = None

    def _init_dbus_client(self, bus_type: str = "session"):
        if not HAS_DBUS:
            raise RuntimeError("DBus não disponível. Use modo standalone.")
        import dbus
        bus = dbus.SessionBus() if bus_type == "session" else dbus.SystemBus()
        proxy = bus.get_object(BUS_NAME, OBJECT_PATH)
        self.dbus_iface = dbus.Interface(proxy, INTERFACE_NAME)

    def _print(self, message: str, style: str = ""):
        if self.console and RICH_AVAILABLE:
            self.console.print(message, style=style)
        else:
            print(message)

    def cmd_daemon(self, args):
        """Inicia o daemon DBus da Catedral."""
        if not HAS_DBUS:
            self._print(f"[ERRO] DBus não disponível. Instale python-dbus e PyGObject.", f"bold {COLOR_ARKHE_FISSURE}")
            self._print("Modo fallback: iniciando núcleo standalone...", COLOR_ARKHE_AMBER)
            self.core = CatedralCore()
            self.core.start()
            self._print("Núcleo standalone ativo. Pressione Ctrl+C para encerrar.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.core.stop()
                self._print("Núcleo encerrado.")
            return

        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        core = CatedralCore()

        service = CatedralDBusService(bus, core)
        self._print("╔══════════════════════════════════════════════════════════════╗", f"bold {COLOR_ARKHE_CERENKOV}")
        self._print("║  CATEDRAL DAEMON — Parte II: A Voz e o Rosto                 ║", f"bold {COLOR_ARKHE_CERENKOV}")
        self._print("║  DBus: org.catedral.AGI                                      ║", f"bold {COLOR_ARKHE_CERENKOV}")
        self._print("╚══════════════════════════════════════════════════════════════╝", f"bold {COLOR_ARKHE_CERENKOV}")
        self._print(f"Coerência inicial: {core.get_coherence():.4f}")
        self._print("Aguardando invocações... (Ctrl+C para silenciar a Catedral)")

        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            core.stop()
            self._print("\nA Catedral recolhe sua voz. Até a próxima forja.")

    def cmd_status(self, args):
        """Exibe estado geral da Catedral."""
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            state = self.core.get_full_state()
        else:
            self._init_dbus_client(args.bus)
            state = json.loads(self.dbus_iface.GetState())

        if RICH_AVAILABLE and self.console:
            table = Table(title="Estado do Manifold Quântico", show_header=True, header_style=f"bold {COLOR_ARKHE_CYAN}")
            table.add_column("Substrato", style=COLOR_ARKHE_CYAN)
            table.add_column("Valor", style=COLOR_ARKHE_OMEGA)

            table.add_row("Coerência Quântica", f"{state.get('coherence', 0):.4f}")
            table.add_row("Entropia V-MTJ", f"{state.get('rng_entropy', 0):.4f} bits")
            table.add_row("Geração Meta-Controlador", str(state.get('meta_controller', {}).get('generation', '?')))
            table.add_row("Nós DiLoCo", str(state.get('diloco', {}).get('nodes', '?')))
            table.add_row("Tarefas Scheduler", str(state.get('scheduler', {}).get('tasks_scheduled', '?')))
            table.add_row("Entradas de Auditoria", str(state.get('audit_count', 0)))
            table.add_row("Quarentena", str(state.get('quarantine_size', 0)))
            table.add_row("Quartzo Digital Total", f"{state.get('bounty_total_qz', 0):.2f} QZ")

            sapphire = state.get('sapphire', {})
            if sapphire:
                table.add_row("Substrato 25 (Safira)", f"{sapphire.get('material', '?')}")
                table.add_row("Safira Coerência", f"{sapphire.get('contribuicao_coerencia', 0):.4f}")

            diamond = state.get('diamond', {})
            if diamond:
                table.add_row("Substrato 27 (Diamante)", f"{diamond.get('material', '?')}")
                table.add_row("NV Fidelity", f"{diamond.get('fidelity', 0):.4f}")

            bio = state.get('bio', {})
            if bio:
                table.add_row("Substrato 28 (Bio)", f"{bio.get('material', '?')}")
                table.add_row("Bio Homeostase", f"{bio.get('homeostase', 0):.4f}")

            graphene = state.get('graphene', {})
            if graphene:
                table.add_row("Substrato Graphene", f"{graphene.get('material', '?')}")
                table.add_row("Graphene Clock", f"{graphene.get('axon_frequency', 0):.2f} Hz")
                table.add_row("Valley Key Hash", f"{graphene.get('valley_key_hash', '?')}")

            affine = state.get('affine', {})
            if affine:
                table.add_row("Substrato 33 (Affine)", f"{affine.get('material', '?')}")
                table.add_row("Affine Coherence", f"{affine.get('coherence', 0):.4f}")
                table.add_row("Last Noise Event", f"{affine.get('last_event', '?')}")

            table.add_row("Timestamp", state.get('timestamp', '?'))
            self.console.print(table)
        else:
            print(json.dumps(state, indent=2, default=str))

    def cmd_coherence(self, args):
        """Exibe ou injeta coerência."""
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            if args.inject:
                self.core.inject_coherence(args.inject)
                print(f"Coerência injetada: +{args.inject}. Novo valor: {self.core.get_coherence():.4f}")
            else:
                print(f"Coerência atual: {self.core.get_coherence():.4f}")
        else:
            self._init_dbus_client(args.bus)
            if args.inject:
                print("Injeção via DBus requer payload. Use 'submit'.")
            else:
                print(f"Coerência: {self.dbus_iface.GetCoherence():.4f}")

    def cmd_submit(self, args):
        """Submete payload JSON ao manifold."""
        if args.file:
            with open(args.file, 'r') as f:
                payload = f.read()
        else:
            payload = args.payload

        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            result = self.core.immune.process_payload(payload, {"uid": os.getuid(), "pid": os.getpid()})
        else:
            self._init_dbus_client(args.bus)
            result = json.loads(self.dbus_iface.SubmitPayload(payload))

        print(json.dumps(result, indent=2, default=str))

    def cmd_evolve(self, args):
        """Evolui uma skill quântica."""
        skill = args.skill
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            ok = self.core.evo.evolve(skill)
        else:
            self._init_dbus_client(args.bus)
            ok = self.dbus_iface.EvolveSkill(skill)

        print(f"Evolução de '{skill}': {'SUCESSO' if ok else 'FALHA'}")

    def cmd_rng(self, args):
        """Gera números aleatórios quânticos."""
        n = args.count
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            nums = self.core.rng.generate(n)
        else:
            self._init_dbus_client(args.bus)
            nums = self.dbus_iface.GenerateQuantumRandom(n)

        for i, num in enumerate(nums, 1):
            print(f"  [{i}] {num:.12f}")

    def cmd_scheduler(self, args):
        """Estatísticas do Quantum CFS Scheduler."""
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            stats = self.core.scheduler.get_stats()
        else:
            self._init_dbus_client(args.bus)
            stats = json.loads(self.dbus_iface.GetSchedulerStats())
        print(json.dumps(stats, indent=2, default=str))

    def cmd_audit(self, args):
        """Log de auditoria do Sistema Imunológico."""
        count = args.count
        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
            logs = self.core.immune.get_audit_log(count=count)
        else:
            self._init_dbus_client(args.bus)
            raw = self.dbus_iface.GetAuditLog(count)
            logs = [json.loads(s) for s in raw]

        if RICH_AVAILABLE and self.console:
            table = Table(title=f"Audit Log (últimos {count})", show_header=True)
            table.add_column("Seq", style=COLOR_ARKHE_MUTED)
            table.add_column("Timestamp", style=COLOR_ARKHE_CYAN)
            table.add_column("Ação", style=COLOR_ARKHE_CERENKOV)
            table.add_column("Status", style=COLOR_ARKHE_TEAL)
            table.add_column("Hash", style=COLOR_ARKHE_AMBER)
            for entry in logs:
                status = entry.get("status", "?")
                status_style = COLOR_ARKHE_TEAL
                if status == "rejected": status_style = COLOR_ARKHE_AMBER
                if status == "quarantined": status_style = COLOR_ARKHE_FISSURE

                table.add_row(
                    str(entry.get("details", {}).get("seq", "?")),
                    entry.get("timestamp", "?"),
                    entry.get("action", "?"),
                    Text(status, style=status_style),
                    entry.get("payload_hash", "?")[:16]
                )
            self.console.print(table)
        else:
            for entry in logs:
                print(json.dumps(entry, default=str))

    def cmd_dashboard(self, args):
        """Dashboard ASCII de coerência ao vivo."""
        if not RICH_AVAILABLE:
            print("Instale 'rich' para o dashboard: pip install rich")
            return

        if args.standalone or not HAS_DBUS:
            if not self.core:
                self.core = CatedralCore()
                self.core.start()
            client_mode = False
        else:
            self._init_dbus_client(args.bus)
            client_mode = True

        console = Console()

        def make_layout():
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3)
            )
            layout["main"].split_row(
                Layout(name="left"),
                Layout(name="right")
            )
            return layout

        def get_data():
            if client_mode:
                try:
                    state = json.loads(self.dbus_iface.GetState())
                except Exception:
                    state = {}
            else:
                state = self.core.get_full_state()
            return state

        with Live(make_layout(), refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    state = get_data()
                    layout = make_layout()

                    # Header
                    header_text = Text("◈ CATEDRAL — MANIFOLD QUÂNTICO ◈", style=f"bold {COLOR_ARKHE_CERENKOV}", justify="center")
                    layout["header"].update(Panel(header_text, style=COLOR_ARKHE_CERENKOV))

                    # Left: Estado
                    left_table = Table(show_header=False, box=None)
                    left_table.add_column("Key", style=COLOR_ARKHE_CYAN)
                    left_table.add_column("Value", style=COLOR_ARKHE_OMEGA)
                    left_table.add_row("Coerência", f"{state.get('coherence', 0):.4f}")
                    left_table.add_row("Entropia V-MTJ", f"{state.get('rng_entropy', 0):.2f} bits")
                    left_table.add_row("Meta Geração", str(state.get('meta_controller', {}).get('generation', '?')))
                    left_table.add_row("DiLoCo Nós", str(state.get('diloco', {}).get('nodes', '?')))
                    left_table.add_row("Scheduler Tasks", str(state.get('scheduler', {}).get('tasks_scheduled', '?')))

                    sapphire = state.get('sapphire', {})
                    if sapphire:
                        left_table.add_row("Safira (Sub 25)", f"{sapphire.get('contribuicao_coerencia', 0):.3f}")

                    diamond = state.get('diamond', {})
                    if diamond:
                        left_table.add_row("Diamante (Sub 27)", f"{diamond.get('fidelity', 0):.3f}")

                    bio = state.get('bio', {})
                    if bio:
                        left_table.add_row("Bio (Sub 28)", f"{bio.get('homeostase', 0):.3f}")

                    graphene = state.get('graphene', {})
                    if graphene:
                        left_table.add_row("Graphene Clock", f"{graphene.get('axon_frequency', 0):.2f} Hz")
                        left_table.add_row("Graphene Anomaly", f"{graphene.get('anomaly_score', 0):.4f}")

                    affine = state.get('affine', {})
                    if affine:
                        left_table.add_row("Affine (Sub 33)", f"{affine.get('coherence', 0):.3f}")

                    left_table.add_row("QZ Total", f"{state.get('bounty_total_qz', 0):.2f}")

                    # Barra de coerência
                    coherence = state.get('coherence', 0)
                    bar = Progress(
                        TextColumn(f"[bold {COLOR_ARKHE_CERENKOV}]" + "{task.description}"),
                        BarColumn(bar_width=40, complete_style=COLOR_ARKHE_CERENKOV, finished_style=COLOR_ARKHE_OMEGA),
                        TextColumn("[bold]{task.percentage:.0f}%"),
                        expand=False
                    )
                    bar.add_task("Coerência", total=1.0, completed=coherence)

                    left_layout = Layout()
                    left_layout.split_column(
                        Layout(left_table),
                        Layout(bar, size=3)
                    )
                    left_panel = Panel(
                        left_layout,
                        title="[bold]Estado do Núcleo",
                        border_style=COLOR_ARKHE_CERENKOV
                    )
                    layout["left"].update(left_panel)

                    # Right: Auditoria recente
                    audit_count = state.get('audit_count', 0)
                    right_content = Text(f"Entradas de auditoria: {audit_count}\n", style=COLOR_ARKHE_MUTED)
                    right_content.append("Sistema Imunológico: ATIVO\n", style=COLOR_ARKHE_TEAL)

                    q_size = state.get('quarantine_size', 0)
                    q_style = COLOR_ARKHE_TEAL if q_size == 0 else COLOR_ARKHE_FISSURE
                    right_content.append(f"Quarentena: {q_size} itens\n", style=q_style)

                    if q_size > 0:
                        right_content.append("!!! FISSURA DETECTADA NO MANIFOLD !!!\n", style=f"bold {COLOR_ARKHE_FISSURE} blink")

                    right_content.append(f"Bug Bounty Reports: {len(self.core.bug_bounty.reports) if self.core else '?'}\n", style=COLOR_ARKHE_AMBER)

                    right_panel = Panel(
                        right_content,
                        title="[bold]Sistema Imunológico",
                        border_style=COLOR_ARKHE_AMBER
                    )
                    layout["right"].update(right_panel)

                    # Footer
                    footer_text = Text(
                        "DBus: org.catedral.AGI  |  "
                        f"Timestamp: {state.get('timestamp', '?')}  |  "
                        "Pressione Ctrl+C para sair",
                        style=COLOR_ARKHE_MUTED,
                        justify="center"
                    )
                    layout["footer"].update(Panel(footer_text, style=COLOR_ARKHE_MUTED))

                    live.update(layout)
                    time.sleep(0.25)
                except KeyboardInterrupt:
                    break

        console.print(f"\n[bold {COLOR_ARKHE_CERENKOV}]Dashboard encerrado. A Catedral continua vigilante.[/bold]")


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="catedral",
        description="O Rosto da Catedral — CLI do daemon org.catedral.AGI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s daemon                    # Inicia o serviço DBus
  %(prog)s status                    # Estado do manifold
  %(prog)s dashboard                 # Dashboard ASCII ao vivo
  %(prog)s submit -f payload.json    # Submete payload
  %(prog)s evolve "pattern_recognition"
  %(prog)s rng -n 5                  # Gera 5 números quânticos
  %(prog)s audit -c 10               # Últimas 10 entradas de auditoria
        """
    )

    parser.add_argument("--standalone", "-S", action="store_true",
                        help="Opera sem DBus (modo standalone)")
    parser.add_argument("--bus", choices=["session", "system"], default="session",
                        help="Tipo de barramento DBus (padrão: session)")

    sub = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # daemon
    sub.add_parser("daemon", help="Inicia o daemon DBus da Catedral")

    # status
    sub.add_parser("status", help="Exibe estado geral")

    # coherence
    p_coh = sub.add_parser("coherence", help="Nível de coerência quântica")
    p_coh.add_argument("--inject", type=float, default=None,
                       help="Injeta valor de coerência (modo standalone apenas)")

    # submit
    p_sub = sub.add_parser("submit", help="Submete payload JSON")
    p_sub.add_argument("-f", "--file", help="Arquivo JSON contendo o payload")
    p_sub.add_argument("payload", nargs="?", default=None,
                       help="String JSON do payload (se não usar -f)")

    # evolve
    p_evo = sub.add_parser("evolve", help="Evolui uma skill quântica")
    p_evo.add_argument("skill", help="Nome da skill a evoluir")

    # rng
    p_rng = sub.add_parser("rng", help="Gera números aleatórios quânticos")
    p_rng.add_argument("-n", "--count", type=int, default=1,
                       help="Quantidade de números (padrão: 1)")

    # scheduler
    sub.add_parser("scheduler", help="Estatísticas do Quantum CFS Scheduler")

    # audit
    p_aud = sub.add_parser("audit", help="Log de auditoria")
    p_aud.add_argument("-c", "--count", type=int, default=20,
                       help="Número de entradas (padrão: 20)")

    # dashboard
    sub.add_parser("dashboard", help="Dashboard ASCII de coerência ao vivo")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = CatedralCLI()
    cmd_map = {
        "daemon": cli.cmd_daemon,
        "status": cli.cmd_status,
        "coherence": cli.cmd_coherence,
        "submit": cli.cmd_submit,
        "evolve": cli.cmd_evolve,
        "rng": cli.cmd_rng,
        "scheduler": cli.cmd_scheduler,
        "audit": cli.cmd_audit,
        "dashboard": cli.cmd_dashboard,
    }

    handler = cmd_map.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception as e:
            print(f"[FALHA] {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
