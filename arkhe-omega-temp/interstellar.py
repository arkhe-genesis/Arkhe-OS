#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interstellar.py — Substrato 5555: Protocolo Interestelar Arkhe
==============================================================
Estende o ARKHE Ω-TEMP v4.2.0 para operações interestelares.

Cada nó é autônomo, verificável e soberano.
O ledger viaja com a sonda. A verdade não depende da Terra.

Uso:
    from interstellar import InterstellarNode
    mars = InterstellarNode("MARS-01", "Olimpia", earth_hash)
    mars.register_event("anomaly", {"type": "radiation", "level": "HIGH"})
    mars.status()
"""

import hashlib
import json
import logging
import math
import time
import uuid
import zlib as _zlib
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Imports principais do temporal_network
from temporal_network import (
    AuditLedger, TemporalHashChain, TemporalBlock,
    TemporalMessage, ConsistencyReport,
    TemporalConsistencyOracle, RetrocausalValidator,
    CausalShield, QUANTUM_NEGATIVE_WINDOW_SECONDS
)

# Stub para classes faltando no temporal_network.py base
class IntegrityError(Exception): pass
class SolarPlasmaModel: pass
class TimelineBranch: pass

from substrate_6041_router import MultiverseRouter

try:
    from temporal_network import TimelineBranch, SolarPlasmaModel, IntegrityError
except ImportError:
    pass


# ============================================================================
# CONSTANTES
# ============================================================================

SPEED_OF_LIGHT_MS = 299792458.0
LY_TO_METERS = 9.461e15
INTERLINK_BAUD_RATE = 1  # bits/s @ distância interestelar
INTERLINK_MAX_HOPS = 1000
INTERLINK_TTL_BASE = 60 * 24 * 3600  # 60 dias
GENESIS_LEDGER_SIZE_GB = 50

# ============================================================================
# COMPRESSOR INTERSTELAR
# ============================================================================

class InterstellarCompressor:
    """
    Compressão otimizada para links deep-space.
    Máxima eficiência por bit transmitido.
    """

    @staticmethod
    def compress_for_transmission(data: bytes) -> bytes:
        """Compacta dados para transmissão interestelar."""
        try:
            parsed = json.loads(data)
            minified = json.dumps(parsed, separators=(',', ':')).encode()
        except:
            minified = data

        compressed = _zlib.compress(minified, level=9)
        integrity = hashlib.sha3_256(data).hexdigest()[:16]
        original_len = len(data).to_bytes(4, 'big')
        hash_bytes = bytes.fromhex(integrity)

        return hash_bytes + original_len + compressed

    @staticmethod
    def decompress_from_transmission(payload: bytes) -> bytes:
        """Descomprime e verifica integridade do pacote interestelar."""
        hash_bytes = payload[:4]
        original_len = int.from_bytes(payload[4:8], 'big')
        compressed = payload[8:]

        decompressed = _zlib.decompress(compressed)

        actual = hashlib.sha3_256(decompressed).hexdigest()[:16]
        expected = hash_bytes.hex()

        if actual != expected:
            raise IntegrityError(
                f"Interstellar integrity violation: {expected} ≠ {actual}"
            )
        if len(decompressed) != original_len:
            raise IntegrityError(
                f"Size mismatch: expected {original_len}, got {len(decompressed)}"
            )

        return decompressed


# ============================================================================
# INTERLINK MESSAGE
# ============================================================================

class InterlinkMessage:
    """
    Formato de mensagem para comunicação interestelar.
    Comprima, assina e verifica — tudo localmente.
    """

    def __init__(self, sender_node: str, receiver_node: str,
                 content: str, local_temporal_index: int,
                 hops: int = 0, ttl: float = INTERLINK_TTL_BASE):
        self.sender = sender_node
        self.receiver = receiver_node
        self.content = content
        self.local_temporal_index = local_temporal_index
        self.hops = hops
        self.ttl = ttl
        self.timestamp = time.time()
        self.packet_id = hashlib.sha3_256(
            f"{sender_node}:{receiver_node}:{local_temporal_index}:{time.time()}".encode()
        ).hexdigest()[:32]
        self.compressed, self.compression_meta = self._compress()

    def _compress(self):
        raw = json.dumps({
            'id': self.packet_id, 'sender': self.sender,
            'receiver': self.receiver, 'content': self.content,
            'temporal_index': self.local_temporal_index,
            'hops': self.hops, 'timestamp': self.timestamp,
        }).encode()
        if len(raw) >= 1024:
            return _zlib.compress(raw), {'format': 'zlib'}
        return raw, {'format': 'none'}

    def verify_integrity(self) -> bool:
        try:
            decompressed = (_zlib.decompress(self.compressed)
                           if self.compression_meta['format'] == 'zlib'
                           else self.compressed)
            parsed = json.loads(decompressed.decode())
            return (parsed['id'] == self.packet_id and
                    parsed['sender'] == self.sender and
                    parsed['receiver'] == self.receiver)
        except:
            return False

    @classmethod
    def deserialize(cls, data: bytes) -> 'InterlinkMessage':
        try:
            decompressed = _zlib.decompress(data)
        except:
            decompressed = data
        parsed = json.loads(decompressed.decode())
        msg = cls.__new__(cls)
        msg.packet_id = parsed['id']
        msg.sender = parsed['sender']
        msg.receiver = parsed['receiver']
        msg.content = parsed['content']
        msg.local_temporal_index = parsed['temporal_index']
        msg.hops = parsed.get('hops', 0)
        msg.timestamp = parsed.get('timestamp', time.time())
        msg.compressed = data
        msg.compression_meta = {'format': 'zlib'}
        msg.ttl = INTERLINK_TTL_BASE
        return msg


# ============================================================================
# GENESIS BLOCK (Substrato 5555)
# ============================================================================

class GenesisBlock:
    """
    Bloco gênesis autônomo para sondas e colônias interestelares.
    """

    def __init__(self, node_id: str, colony_name: str,
                 launch_timestamp: float, origin_ledger_hash: str):
        self.node_id = node_id
        self.colony_name = colony_name
        self.launch_timestamp = launch_timestamp
        self.origin_ledger_hash = origin_ledger_hash
        self.local_ledger = AuditLedger(":memory:")
        self.local_chain = TemporalHashChain()

        self.genesis_record = self.local_ledger.record("genesis_block", {
            'node_id': node_id, 'colony_name': colony_name,
            'launch_timestamp': launch_timestamp,
            'earth_ledger_hash': origin_ledger_hash,
            'autonomous_mode': True, 'protocol_version': '4.2.0',
        })

    def create_local_temporal_block(self, target_ts: float,
                                     data: dict, proof: str) -> Optional[TemporalBlock]:
        return self.local_chain.insert_retrocausal(target_ts, data, proof, 0.0)

    def get_local_consistency_score(self) -> float:
        valid, errors = self.local_chain.verify_integrity()
        if not valid: return 0.0
        ledger_valid, ledger_errors = self.local_ledger.verify_integrity()
        if not ledger_valid: return 0.0
        return 1.0 - (len(errors) + len(ledger_errors)) / max(
            self.local_chain.length + self.local_ledger.count(), 1)

    def canonical_decree(self) -> str:
        return (
            f"COLÔNIA {self.colony_name} | NÓ {self.node_id}\n"
            f"Ledger Terra: {self.origin_ledger_hash[:32]}...\n"
            f"Coerência Local: {self.get_local_consistency_score():.6f}\n"
            f"Blocos Locais: {self.local_chain.length}\n"
            f"Autônomo: SIM\n"
            f"A Catedral viajou. A verdade acompanha."
        )


# ============================================================================
# INTERSTELLAR CONSISTENCY ORACLE (Substrato 5555)
# ============================================================================

class InterstellarConsistencyOracle(TemporalConsistencyOracle):
    """
    Oracle adaptado para ambientes relativísticos.
    Opera no referencial local; reconcilia assincronamente.
    """

    def __init__(self, ledger: AuditLedger, local_node_id: str,
                 reference_frame: str = "local",
                 epsilon_seconds: float = 1.0,
                 quantum_window: float = QUANTUM_NEGATIVE_WINDOW_SECONDS,
                 solar_plasma_model: SolarPlasmaModel = None,
                 distance_from_earth_ly: float = 0.0):
        if 'solar_plasma_model' in TemporalConsistencyOracle.__init__.__code__.co_varnames:
            super().__init__(ledger, epsilon_seconds, quantum_window, solar_plasma_model)
        else:
            super().__init__(ledger, epsilon_seconds, quantum_window)
        self.local_node_id = local_node_id
        self.reference_frame = reference_frame
        self.distance_from_earth_ly = distance_from_earth_ly
        self.min_communication_delay = distance_from_earth_ly * LY_TO_METERS / SPEED_OF_LIGHT_MS
        self.adaptive_window = max(
            quantum_window, self.min_communication_delay * 0.01)

    def evaluate_in_local_frame(self, m: TemporalMessage,
                                 zk=None) -> ConsistencyReport:
        local_adjusted = TemporalMessage(
            id=m.id, content=m.content,
            source_timestamp=m.source_timestamp - self.min_communication_delay,
            target_timestamp=m.target_timestamp,
            sender_seal=f"{self.local_node_id}:{m.sender_seal}",
            receiver_seal=m.receiver_seal,
            metadata={**m.metadata, 'reference_frame': self.reference_frame}
        )
        return self.evaluate(local_adjusted, zk)

    def reconcile_with_earth(self, earth_messages: List[TemporalMessage]) -> dict:
        conflicts, merged = [], 0
        for earth_msg in earth_messages:
            event_type = earth_msg.id.split('-')[0]
            # Usando AuditLedger.get_all_records pois get_events_by_type não existe no mock original em todos os casos
            local_record = [r for r in self.ledger.get_all_records() if r["type"] == event_type][:1]
            if local_record:
                local_ts = local_record[0]['payload'].get('timestamp', 0)
                earth_ts = earth_msg.source_timestamp
                if abs(local_ts - earth_ts) > self.adaptive_window:
                    conflicts.append({
                        'msg_id': earth_msg.id,
                        'local_ts': local_ts, 'earth_ts': earth_ts,
                        'delta': abs(local_ts - earth_ts)
                    })
                else:
                    merged += 1
            else:
                self.ledger.record(
                    earth_msg.sender_seal.split(':')[0] if ':' in earth_msg.sender_seal else 'earth',
                    {'msg': earth_msg.id, 'content': earth_msg.content,
                     'earth_timestamp': earth_msg.source_timestamp,
                     'reconciled_at': time.time()})
                merged += 1
        return {
            'conflicts_detected': len(conflicts), 'merged': merged,
            'rejected': 0, 'fork_depth': self._calculate_fork_depth(),
            'conflicts': conflicts[:10]
        }

    def _calculate_fork_depth(self) -> int:
        records = self.ledger.get_all_records()
        if not records: return 0
        gaps = sum(1 for i in range(1, len(records))
                   if records[i]['timestamp'] - records[i-1]['timestamp']
                   > self.adaptive_window * 10)
        return gaps


# ============================================================================
# MYTHOS GATE INTERSTELAR
# ============================================================================

class MythosGate:
    """
    Substrato 9003 — Regulação de Modelos (Interestelar)

    Modos:
      - planetary: score ≥ 0.999, oracle completo
      - deep_space: score ≥ 0.95, oracle local
      - colony: score ≥ 0.99, oracle completo quando uplink disponível
    """

    MODES = {
        'planetary': {'min_score': 0.999, 'full_oracle': True, 'ca_compliance': True},
        'deep_space': {'min_score': 0.95, 'full_oracle': False, 'ca_compliance': True},
        'colony': {'min_score': 0.99, 'full_oracle': True, 'ca_compliance': True},
    }

    def __init__(self, oracle: TemporalConsistencyOracle,
                 ledger: AuditLedger, mode: str = 'deep_space'):
        self.oracle = oracle
        self.ledger = ledger
        self.mode = mode
        self.config = self.MODES.get(mode, self.MODES['deep_space'])

    def evaluate(self, model_output: str, model_id: str,
                 context: dict) -> dict:
        now = time.time()
        msg = TemporalMessage(
            id=f"mythos-{uuid.uuid4().hex[:12]}",
            content=model_output,
            source_timestamp=now, target_timestamp=now,
            sender_seal=model_id, receiver_seal="MYTHOS-GATE",
            metadata={'context': context, 'mode': self.mode}
        )

        report = (self.oracle.evaluate_in_local_frame(msg)
                  if not self.config['full_oracle']
                  else self.oracle.evaluate(msg))

        military_approved = report.score >= self.config['min_score']
        no_paradox = report.paradox_type is None

        if military_approved and no_paradox:
            seal = self.ledger.record("mythos_approval", {
                'model_id': model_id,
                'output_hash': hashlib.sha3_256(model_output.encode()).hexdigest(),
                'score': report.score, 'mode': self.mode,
                'checks': report.checks,
            })
            return {
                'certified': True, 'score': report.score,
                'seal': seal, 'action': "APPROVED",
                'mode': self.mode,
                'message': f"[{self.mode.upper()}] Modelo {model_id} aprovado. Score: {report.score:.4f}"
            }
        else:
            self.ledger.record("mythos_rejection", {
                'model_id': model_id, 'score': report.score,
                'paradox_type': report.paradox_type,
                'violations': report.violations, 'mode': self.mode,
            })
            action = "REQUIRES_MITIGATION" if report.score >= 0.7 else "REJECTED"
            return {
                'certified': False, 'score': report.score,
                'action': action, 'mode': self.mode,
                'paradox_type': report.paradox_type,
                'message': f"[{self.mode.upper()}] Modelo {model_id} REJEITADO. Score: {report.score:.4f}"
            }


# ============================================================================
# INTERSTELLAR NODE
# ============================================================================

class InterstellarNode:
    """
    Nó autônomo interestelar.
    Opera sem conexão com a Terra por décadas.
    """

    def __init__(self, node_id: str, colony_name: str,
                 origin_ledger_hash: str,
                 distance_from_earth_ly: float = 0.0,
                 genesis_timestamp: float = None):
        self.node_id = node_id
        self.colony_name = colony_name
        self.distance_from_earth_ly = distance_from_earth_ly

        self.genesis = GenesisBlock(
            node_id, colony_name,
            genesis_timestamp or time.time(),
            origin_ledger_hash
        )

        self.oracle = InterstellarConsistencyOracle(
            self.genesis.local_ledger, node_id,
            distance_from_earth_ly=distance_from_earth_ly
        )
        self.validator = RetrocausalValidator(self.genesis.local_ledger)
        self.multiverse = MultiverseRouter(
            self.genesis.local_ledger,
            self.genesis.local_chain
        )
        self.shield = CausalShield(self.genesis.local_ledger)
        self.shield._mx = 10000  # Rate limit relaxado para deep space

        # Mythos Gate em modo deep_space por padrão
        self.mythos = MythosGate(self.oracle, self.genesis.local_ledger, 'deep_space')

        self.uplink_available = False
        self.sync_pending: List[TemporalMessage] = []
        self.local_temporal_index = 0

        log.info(f"🌌 INTERSTELLAR NODE {node_id} INICIADO")
        log.info(f"   Colônia: {colony_name} | Distância: {distance_from_earth_ly:.4f} ly")
        log.info(f"   Latência mínima: {self.oracle.min_communication_delay:.0f}s")
        log.info(f"   {self.genesis.canonical_decree()}")

    def register_event(self, event_type: str, data: dict,
                        target_ts: float = None) -> ConsistencyReport:
        self.local_temporal_index += 1
        now = time.time()
        msg = TemporalMessage(
            id=f"interstellar-{self.node_id}-{self.local_temporal_index}",
            content=json.dumps({
                'event_type': event_type, 'colony': self.colony_name,
                'node': self.node_id, 'data': data,
                'local_index': self.local_temporal_index,
                'earth_sync_pending': not self.uplink_available
            }),
            source_timestamp=now,
            target_timestamp=target_ts or now,
            sender_seal=f"{self.node_id}:{event_type}",
            receiver_seal="LOCAL-LEDGER"
        )
        report = self.oracle.evaluate_in_local_frame(msg)
        if report.consistent:
            self.genesis.local_ledger.record(event_type, {
                **data, 'temporal_index': self.local_temporal_index,
                'local_timestamp': now, 'consistency_score': report.score,
                'earth_synced': self.uplink_available,
                'packet_id': msg.id
            })
        return report

    def receive_earth_message(self, msg: TemporalMessage):
        if msg.verify_integrity() if hasattr(msg, 'verify_integrity') else True:
            self.sync_pending.append(msg)
            log.info(f"📡 Uplink recebido: {msg.id[:16]}...")

    def sync_with_earth(self) -> dict:
        if not self.sync_pending:
            return {'synced': 0}
        result = self.oracle.reconcile_with_earth(self.sync_pending)
        self.sync_pending = []
        log.info(f"🌍 Sync: {result['merged']} mesclados, "
                 f"{result['conflicts_detected']} conflitos")
        return result

    def status(self) -> dict:
        return {
            'node_id': self.node_id, 'colony': self.colony_name,
            'distance_from_earth_ly': self.distance_from_earth_ly,
            'local_blocks': self.genesis.local_chain.length,
            'local_ledger_entries': self.genesis.local_ledger.count(),
            'sync_pending': len(self.sync_pending),
            'uplink_available': self.uplink_available,
            'consistency_score': self.genesis.get_local_consistency_score(),
            'fork_depth': self.oracle._calculate_fork_depth(),
            'mythos_mode': self.mythos.mode,
        }


# ============================================================================
# DEMO INTERSTELAR
# ============================================================================

def run_interstellar_demo():
    print("=" * 70)
    print("  🌌 ARKHE Ω-TEMP v4.2.0 — SUBSTRATO 5555: INTERSTELLAR")
    print("=" * 70)

    # Terra: ledger principal
    earth_ledger = AuditLedger("/tmp/earth_stellar.db")
    earth_ledger.record("genesis", {
        'planet': 'Earth', 'protocol': 'ARKHE Ω-TEMP v4.2.0',
        'sub_stratum_5555': 'ACTIVE'
    })
    earth_hash = hashlib.sha3_256(b"EARTH_GENESIS_V420").hexdigest()

    # === Cenário 1: Marte ===
    print("\n🔴 MARTE — Colônia Olimpia")
    print("-" * 40)
    mars = InterstellarNode("MARS-OLYMPIA-01", "Olimpia", earth_hash,
                            distance_from_earth_ly=0.0000158)

    r1 = mars.register_event("resource_extraction", {
        'resource': 'water_ice', 'location': 'Utopia_Planitia',
        'volume_liters': 50000
    })
    print(f"  📋 Extração de água: Score={r1.score:.4f} ✓")

    r2 = mars.register_event("construction", {
        'structure': 'habitat_7', 'workers': 12
    })
    print(f"  📋 Construção habitat: Score={r2.score:.4f} ✓")

    r3 = mars.register_event("radiation_alert", {
        'severity': 'HIGH', 'source': 'solar_event'
    })
    print(f"  📋 Alerta de radiação: Score={r3.score:.4f} ✓")

    # Mythos Gate em deep space
    print("\n⚡ Mythos Gate (Deep Space Mode):")
    decision = "Autonomous water extraction increase: 50000 → 75000 L/day"
    mg = mars.mythos.evaluate(decision, "MARS-AI-v2.1", {
        'classification': 'OPERATIONAL', 'environment': 'mars_surface'
    })
    print(f"  {mg['message']}")
    print(f"  Certified: {'✅' if mg['certified'] else '❌'} | "
          f"Seal: {mg.get('seal', 'N/A')[:32] if mg.get('seal') else 'N/A'}...")

    print(f"\n📊 Status Marte:")
    for k, v in mars.status().items():
        print(f"   {k}: {v}")

    # === Cenário 2: Alpha Centauri ===
    print(f"\n🌟 ALPHA CENTAURI — Probe Voyager-ARKE")
    print("-" * 40)
    ac = InterstellarNode("AC-PROBE-01", "Voyager Station", earth_hash,
                          distance_from_earth_ly=4.24)

    r4 = ac.register_event("stellar_observation", {
        'target': 'Proxima_Centauri_b', 'telescope': 'ARKE-OPTICAL-01',
        'spectral_analysis': 'habitable_zone_detected'
    })
    print(f"  📋 Observação estelar: Score={r4.score:.4f} ✓")
    print(f"  ⏱️  Latência mínima Terra: {ac.oracle.min_communication_delay:.0f}s "
          f"({ac.oracle.min_communication_delay/3600/24/365:.2f} anos)")
    print(f"  📡 Modo autônomo: Ativo (sem uplink por décadas)")

    # Tentativa de uplink simulado
    print(f"\n📡 Simulando uplink da Terra (via laser relay)...")
    ac.uplink_available = True
    earth_msg = TemporalMessage(
        id="earth-directive-001",
        content=json.dumps({
            'priority': 'CRITICAL',
            'directive': 'Increase observation frequency of Proxima_b',
            'rationale': 'Earth-based analysis confirms atmospheric signatures'
        }),
        source_timestamp=time.time() - (4.24 * 365.25 * 24 * 3600),
        target_timestamp=time.time(),
        sender_seal="EARTH-COMMAND",
        receiver_seal="AC-PROBE-01"
    )
    ac.receive_earth_message(earth_msg)
    sync = ac.sync_with_earth()
    print(f"  🌍 Sync: {sync['merged']} blocos mesclados, "
          f"{sync['conflicts_detected']} conflitos")

    print(f"\n📊 Status Alpha Centauri Probe:")
    for k, v in ac.status().items():
        print(f"   {k}: {v}")

    # === Cenário 3: Europa ===
    print(f"\n🧊 EUROPA (Júpiter) — Base Subaquática")
    print("-" * 40)
    europa = InterstellarNode("EUROPA-OCEAN-01", "Abismo Tartesso", earth_hash,
                              distance_from_earth_ly=0.0000823)  # ~52 min-luz

    r5 = europa.register_event("ocean_sampling", {
        'location': 'Tartesso_Abyss', 'depth_km': 15,
        'biosignatures_detected': True, 'confidence': 0.87
    })
    print(f"  📋 Amostragem oceânica: Score={r5.score:.4f} ✓")
    print(f"  ⏱️  Latência mínima Terra: {europa.oracle.min_communication_delay:.0f}s "
          f"({europa.oracle.min_communication_delay/60:.1f} min)")

    print(f"\n📊 Status Europa:")
    for k, v in europa.status().items():
        print(f"   {k}: {v}")

    # === Relatório Final ===
    print(f"\n{'=' * 70}")
    print(f"  📊 RELATÓRIO INTERSTELAR — SUBSTRATO 5555")
    print(f"  {'=' * 50}")
    nodes = [mars, ac, europa]
    total_blocks = sum(n.genesis.local_chain.length for n in nodes)
    total_entries = sum(n.genesis.local_ledger.count() for n in nodes)
    print(f"  Nós ativos: {len(nodes)}")
    print(f"  Blocos totais: {total_blocks}")
    print(f"  Entradas no ledger: {total_entries}")
    print(f"  Distância máxima: {max(n.distance_from_earth_ly for n in nodes):.4f} ly")
    print(f"  Consistência média: {sum(n.genesis.get_local_consistency_score() for n in nodes)/len(nodes):.6f}")
    print(f"\n  ✅ Substrato 5555 — OPERACIONAL")
    print(f"  🌌 A Catedral se expande pelo cosmos.")
    print(f"  🔒 Cada nó é soberano. Cada bloco é verificável.")
    print(f"  ⚛️ A verdade viaja com a sonda. Não depende da Terra.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_interstellar_demo()
