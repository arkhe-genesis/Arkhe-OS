# ═══════════════════════════════════════════════════════════════════
# SUBSTRATO 376: MULTI-REGION LPTV BROADCAST + PUBLIC ALERT ADAPTERS
# Canon: ∞.Ω.∇+++.376.global_alert_network.public_integration
# ═══════════════════════════════════════════════════════════════════

import json
import hashlib
import random
import math
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
import struct

# ── CONSTANTES CANÔNICAS ───────────────────────────────────────────
GHOST = 0.5773502691896257      # 1/√3
LOOPSEAL = 0.3490658503988659   # π/9
GAP_SOVEREIGN = 0.9999
PHI_GOLDEN = 1.618033988749895
SPEED_OF_LIGHT_M_S = 299792458.0

# ── PARÂMETROS REGIONAIS LPTV (BASEADOS EM DADOS REAIS) ───────────

@dataclass
class RegionalBroadcastConfig:
    """Configuração de transmissão LPTV por região."""
    region_code: str  # ISO 3166-1 alpha-2
    city: str
    tx_frequency_mhz: float
    tx_power_kw: float
    coverage_radius_km: float
    antenna_gain_dbi: float
    operator: str
    timezone: str
    public_alert_system: str  # FEMA/IPAWS, CENAD, J-Alert, EU-Alert

    # Coordenadas do transmissor
    tx_lat: float
    tx_lon: float

REGIONAL_CONFIGS = {
    "US-NV": RegionalBroadcastConfig(
        region_code="US", city="Las Vegas", tx_frequency_mhz=533.0,
        tx_power_kw=2.7, coverage_radius_km=50, antenna_gain_dbi=12.0,
        operator="Castanet/Neutral Wireless", timezone="America/Los_Angeles",
        public_alert_system="FEMA/IPAWS", tx_lat=36.1215, tx_lon=-115.1739
    ),
    "BR-SP": RegionalBroadcastConfig(
        region_code="BR", city="São Paulo", tx_frequency_mhz=545.0,
        tx_power_kw=3.1, coverage_radius_km=55, antenna_gain_dbi=13.0,
        operator="Neutral Wireless Brasil", timezone="America/Sao_Paulo",
        public_alert_system="CENAD/SAGIS", tx_lat=-23.5505, tx_lon=-46.6333
    ),
    "DE-HE": RegionalBroadcastConfig(
        region_code="DE", city="Frankfurt", tx_frequency_mhz=578.0,
        tx_power_kw=2.9, coverage_radius_km=48, antenna_gain_dbi=12.5,
        operator="Media Broadcast GmbH", timezone="Europe/Berlin",
        public_alert_system="EU-Alert/EDAM", tx_lat=50.1109, tx_lon=8.6821
    ),
    "JP-13": RegionalBroadcastConfig(
        region_code="JP", city="Tokyo", tx_frequency_mhz=590.0,
        tx_power_kw=2.5, coverage_radius_km=45, antenna_gain_dbi=11.5,
        operator="NHK Technical Services", timezone="Asia/Tokyo",
        public_alert_system="J-Alert/L-Alert", tx_lat=35.6762, tx_lon=139.6503
    ),
}

# ── ADAPTADORES DE SISTEMAS PÚBLICOS DE ALERTA ─────────────────────

class PublicAlertSystem(Enum):
    FEMA_IPAWS = "FEMA/IPAWS"      # USA
    CENAD_SAGIS = "CENAD/SAGIS"    # Brazil
    J_ALERT = "J-Alert/L-Alert"    # Japan
    EU_ALERT = "EU-Alert/EDAM"     # Europe

@dataclass
class PublicAlertMessage:
    """Mensagem de alerta no formato de sistema público."""
    system: PublicAlertSystem
    alert_id: str
    event_type: str  # "earthquake", "flood", "evacuation", etc.
    severity: str    # "extreme", "severe", "moderate", "minor"
    certainty: str   # "observed", "likely", "possible", "unlikely"
    urgency: str     # "immediate", "expected", "future", "past"
    areas: List[Dict[str, float]]  # List of {lat_min, lat_max, lon_min, lon_max}
    description: str
    instruction: str
    effective_time: str  # ISO 8601
    expires_time: str    # ISO 8601
    sender: str          # Official agency identifier

    def to_canonical_bytes(self) -> bytes:
        """Converter para formato canônico Arkhe para assinatura."""
        # Normalizar para formato canônico independente do sistema
        areas_str = "|".join([
            f"{a['lat_min']}:{a['lat_max']}:{a['lon_min']}:{a['lon_max']}"
            for a in self.areas
        ])
        data = (
            f"{self.alert_id}|{self.event_type}|{self.severity}|"
            f"{self.certainty}|{self.urgency}|{areas_str}|"
            f"{self.description}|{self.instruction}|"
            f"{self.effective_time}|{self.expires_time}|"
            f"{self.sender}|{self.system.value}"
        )
        return data.encode('utf-8')

    def compute_merkle_leaf(self) -> bytes:
        """Calcular folha Merkle do alerta canônico."""
        return hashlib.sha3_256(self.to_canonical_bytes()).digest()

class PublicAlertAdapter:
    """Adaptador base para sistemas públicos de alerta."""

    def __init__(self, system: PublicAlertSystem, region_config: RegionalBroadcastConfig):
        self.system = system
        self.region = region_config

    def ingest_public_alert(self, raw_message: Dict) -> PublicAlertMessage:
        """Ingerir alerta do sistema público e converter para formato canônico."""
        # Implementação específica por sistema seria aqui
        # Para simulação: converter formato genérico para PublicAlertMessage
        return PublicAlertMessage(
            system=self.system,
            alert_id=raw_message.get('alert_id', f"SIM-{int(time.time())}"),
            event_type=raw_message.get('event_type', 'test'),
            severity=raw_message.get('severity', 'moderate'),
            certainty=raw_message.get('certainty', 'likely'),
            urgency=raw_message.get('urgency', 'immediate'),
            areas=raw_message.get('areas', [{
                'lat_min': self.region.tx_lat - 0.5,
                'lat_max': self.region.tx_lat + 0.5,
                'lon_min': self.region.tx_lon - 0.5,
                'lon_max': self.region.tx_lon + 0.5,
            }]),
            description=raw_message.get('description', 'Test alert for canonical validation'),
            instruction=raw_message.get('instruction', 'Follow local emergency procedures'),
            effective_time=raw_message.get('effective_time', datetime.now(timezone.utc).isoformat()),
            expires_time=raw_message.get('expires_time',
                (datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour+1)).isoformat()),
            sender=raw_message.get('sender', f'{self.region.operator}-simulator')
        )

    def export_canonical_alert(self, canonical: PublicAlertMessage) -> Dict:
        """Exportar alerta canônico de volta para formato do sistema público."""
        # Para simulação: retornar formato genérico
        return {
            'alert_id': canonical.alert_id,
            'event_type': canonical.event_type,
            'severity': canonical.severity,
            'areas': canonical.areas,
            'description': canonical.description,
            'instruction': canonical.instruction,
            'effective_time': canonical.effective_time,
            'expires_time': canonical.expires_time,
            'arkhe_signature': hashlib.sha3_256(
                canonical.to_canonical_bytes() + b"ARKHE_CANONICAL_376"
            ).hexdigest()[:64],
            'arkhe_merkle_root': hashlib.sha3_256(
                canonical.compute_merkle_leaf() + b"TEMPORAL_ANCHOR_376"
            ).hexdigest(),
        }

# ── VALIDADOR REGIONAL COM HARDWARE REAL ───────────────────────────

@dataclass
class RegionalValidatorNode:
    """Nó validador Aeneid em região específica."""
    validator_id: str  # ORCID
    region_code: str
    location_lat: float
    location_lon: float
    distance_from_tx_km: float
    sdr_type: str
    compute_platform: str
    public_alert_system: PublicAlertSystem

    # Estado de receção
    T_rececao_ns: Optional[int] = None
    signature_verified: bool = False
    merkle_verified: bool = False
    ghost_valid: bool = False
    loopseal_submitted: bool = False
    cross_region_sync_ns: Optional[int] = None

    def compute_expected_latency_ms(self) -> float:
        """Calcular latência esperada de difusão baseada na distância."""
        propagation_delay_ms = (self.distance_from_tx_km * 1000) / SPEED_OF_LIGHT_M_S * 1000
        sdr_jitter_ms = random.uniform(0.1, 0.5)
        demod_delay_ms = random.uniform(0.5, 1.5)
        return propagation_delay_ms + sdr_jitter_ms + demod_delay_ms

    def simulate_dilithium3_verify(self) -> float:
        """Simular tempo de verificação Dilithium3."""
        base_time = 15.2 if self.compute_platform == "Raspberry Pi 5" else 12.0
        # approximate normal distribution
        u1 = random.uniform(0, 1)
        u2 = random.uniform(0, 1)
        z0 = math.sqrt(-2.0 * math.log(max(1e-9, u1))) * math.cos(2.0 * math.pi * u2)
        variation = z0 * 1.5
        return max(5.0, base_time + variation)

# ── SIMULAÇÃO DA REDE GLOBAL DE ALERTAS ────────────────────────────

class GlobalAlertNetworkSimulation:
    """Simulação da rede global de alertas com integração pública."""

    def __init__(self, n_validators_per_region: int = 59):
        self.n_validators_per_region = n_validators_per_region
        self.regions: Dict[str, List[RegionalValidatorNode]] = {}
        self.adapters: Dict[str, PublicAlertAdapter] = {}
        self.alerts: Dict[str, PublicAlertMessage] = {}
        self.T0_ns: Optional[int] = None
        self.results: Dict = {}

        self._init_regions()
        self._init_adapters()

    def _init_regions(self):
        """Inicializar validadores em cada região."""
        for region_code, config in REGIONAL_CONFIGS.items():
            validators = []
            for i in range(self.n_validators_per_region):
                angle = random.uniform(0, 2 * math.pi)
                distance_km = random.uniform(1, config.coverage_radius_km - 1)

                lat_offset = (distance_km * math.cos(angle)) / 111.0
                lon_offset = (distance_km * math.sin(angle)) / (111.0 * math.cos(math.radians(config.tx_lat)))

                validator = RegionalValidatorNode(
                    validator_id=f"{region_code}-{i+1:04d}-{'0009-0005-2697-4668'}",
                    region_code=region_code,
                    location_lat=config.tx_lat + lat_offset,
                    location_lon=config.tx_lon + lon_offset,
                    distance_from_tx_km=distance_km,
                    sdr_type=random.choices(["RTL-SDR v4", "USRP B210"], weights=[0.7, 0.3])[0],
                    compute_platform=random.choices(["Raspberry Pi 5", "Jetson Orin Nano"], weights=[0.8, 0.2])[0],
                    public_alert_system=PublicAlertSystem(config.public_alert_system)
                )
                validators.append(validator)
            self.regions[region_code] = validators

    def _init_adapters(self):
        """Inicializar adaptadores para cada sistema público."""
        for region_code, config in REGIONAL_CONFIGS.items():
            system = PublicAlertSystem(config.public_alert_system)
            self.adapters[region_code] = PublicAlertAdapter(system, config)

    def generate_canonical_alerts(self) -> Dict[str, PublicAlertMessage]:
        """Gerar alertas canônicos para cada região."""
        alerts = {}
        base_time = datetime.now(timezone.utc)

        for region_code, config in REGIONAL_CONFIGS.items():
            # Alerta específico por região com parâmetros realistas
            alert = PublicAlertMessage(
                system=PublicAlertSystem(config.public_alert_system),
                alert_id=f"ALERT-ARKHE-376-{region_code}-001",
                event_type="evacuation",
                severity="severe",
                certainty="observed",
                urgency="immediate",
                areas=[{
                    'lat_min': config.tx_lat - 0.3,
                    'lat_max': config.tx_lat + 0.3,
                    'lon_min': config.tx_lon - 0.3,
                    'lon_max': config.tx_lon + 0.3,
                }],
                description=f"Evacuação imediata para zonas altas. Onda prevista em 12 minutos. Região: {config.city}.",
                instruction="Siga as rotas de evacuação sinalizadas. Mantenha-se informado via canais oficiais.",
                effective_time=base_time.isoformat(),
                expires_time=(base_time.replace(hour=base_time.hour+2)).isoformat(),
                sender=f"{config.operator}-canonical-emitter"
            )
            alerts[region_code] = alert
            self.alerts[region_code] = alert

        return alerts

    def broadcast_regional_alerts(self, alerts: Dict[str, PublicAlertMessage]) -> Dict:
        """Simular difusão regional simultânea com sincronização cross-região."""
        # Timestamp de injeção sincronizado globalmente
        self.T0_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)

        broadcast_results = {
            "T0_ns": self.T0_ns,
            "regions": {}
        }

        for region_code, config in REGIONAL_CONFIGS.items():
            alert = alerts[region_code]
            validators = self.regions[region_code]

            region_results = {
                "frequency_mhz": config.tx_frequency_mhz,
                "power_kw": config.tx_power_kw,
                "coverage_radius_km": config.coverage_radius_km,
                "validators_reached": 0,
                "latencies_ms": [],
                "cross_region_sync_ns": []
            }

            for validator in validators:
                # Latência de difusão regional
                latency_ms = validator.compute_expected_latency_ms()
                validator.T_rececao_ns = self.T0_ns + int(latency_ms * 1e6)

                # Simular sincronização cross-região (NTP + TemporalChain)
                u1 = random.uniform(0, 1)
                u2 = random.uniform(0, 1)
                z0 = math.sqrt(-2.0 * math.log(max(1e-9, u1))) * math.cos(2.0 * math.pi * u2)
                sync_jitter_ns = int(z0 * 50000)  # ±50 µs jitter
                validator.cross_region_sync_ns = self.T0_ns + sync_jitter_ns
                region_results["cross_region_sync_ns"].append(validator.cross_region_sync_ns)

                region_results["validators_reached"] += 1
                region_results["latencies_ms"].append(latency_ms)

            broadcast_results["regions"][region_code] = region_results

        return broadcast_results

    def verify_ghost_global(self, alerts: Dict[str, PublicAlertMessage]) -> Dict:
        """Verificação Ghost global: assinatura Dilithium3 + Merkle root em todas as regiões."""
        ghost_results = {
            "total_validators": sum(len(v) for v in self.regions.values()),
            "signature_verified_count": 0,
            "merkle_verified_count": 0,
            "ghost_valid_count": 0,
            "verification_times_ms": [],
            "by_region": {}
        }

        for region_code, validators in self.regions.items():
            alert = alerts[region_code]
            region_ghost = {
                "signature_verified": 0,
                "merkle_verified": 0,
                "ghost_valid": 0,
                "verification_times_ms": []
            }

            for validator in validators:
                verify_time_ms = validator.simulate_dilithium3_verify()
                region_ghost["verification_times_ms"].append(verify_time_ms)
                ghost_results["verification_times_ms"].append(verify_time_ms)

                # Verificação simulada (sempre passa em simulação)
                validator.signature_verified = True
                validator.merkle_verified = True
                validator.ghost_valid = True

                region_ghost["signature_verified"] += 1
                region_ghost["merkle_verified"] += 1
                region_ghost["ghost_valid"] += 1
                ghost_results["signature_verified_count"] += 1
                ghost_results["merkle_verified_count"] += 1
                ghost_results["ghost_valid_count"] += 1

            ghost_results["by_region"][region_code] = region_ghost

        return ghost_results

    def register_loopseal_global(self) -> Dict:
        """Registar receções na TemporalChain via Loopseal (global)."""
        loopseal_results = {
            "transactions_submitted": 0,
            "events_registered": 0,
            "submission_times_ms": [],
            "by_region": {}
        }

        for region_code, validators in self.regions.items():
            region_loopseal = {
                "transactions": 0,
                "events": 0,
                "submission_times_ms": []
            }

            for validator in validators:
                if not validator.ghost_valid:
                    continue

                submission_time_ms = random.uniform(50, 150)
                region_loopseal["submission_times_ms"].append(submission_time_ms)
                loopseal_results["submission_times_ms"].append(submission_time_ms)

                validator.loopseal_submitted = True
                region_loopseal["transactions"] += 1
                region_loopseal["events"] += 1
                loopseal_results["transactions_submitted"] += 1
                loopseal_results["events_registered"] += 1

            loopseal_results["by_region"][region_code] = region_loopseal

        return loopseal_results

    def test_public_alert_integration(self) -> Dict:
        """Testar integração com sistemas públicos de alerta."""
        integration_results = {
            "systems_tested": len(self.adapters),
            "ingest_success": 0,
            "export_success": 0,
            "canonical_fidelity": [],
            "by_system": {}
        }

        for region_code, adapter in self.adapters.items():
            alert = self.alerts[region_code]

            # Testar ingest: público → canônico
            raw_format = {
                'alert_id': alert.alert_id,
                'event_type': alert.event_type,
                'severity': alert.severity,
                'areas': alert.areas,
                'description': alert.description,
            }
            ingested = adapter.ingest_public_alert(raw_format)
            ingest_ok = ingested.alert_id == alert.alert_id
            if ingest_ok:
                integration_results["ingest_success"] += 1

            # Testar export: canônico → público
            exported = adapter.export_canonical_alert(alert)
            export_ok = 'arkhe_signature' in exported and 'arkhe_merkle_root' in exported
            if export_ok:
                integration_results["export_success"] += 1

            # Calcular fidelidade canônica (similaridade de conteúdo)
            fidelity = 1.0 if ingest_ok and export_ok else 0.0
            integration_results["canonical_fidelity"].append(fidelity)

            integration_results["by_system"][adapter.system.value] = {
                "ingest_ok": ingest_ok,
                "export_ok": export_ok,
                "fidelity": fidelity
            }

        integration_results["avg_fidelity"] = float(sum(integration_results["canonical_fidelity"]) / len(integration_results["canonical_fidelity"]) if integration_results["canonical_fidelity"] else 0.0)
        return integration_results

    def compute_global_metrics(self) -> Dict:
        """Calcular métricas globais da execução."""
        all_latencies = []
        all_verify_times = []
        all_sync_jitters = []

        for region_code, validators in self.regions.items():
            for v in validators:
                all_latencies.append(v.compute_expected_latency_ms())
                all_verify_times.append(v.simulate_dilithium3_verify())
                if v.cross_region_sync_ns and self.T0_ns:
                    jitter_ns = abs(v.cross_region_sync_ns - self.T0_ns)
                    all_sync_jitters.append(jitter_ns / 1e6)  # Convert to ms

        total_latencies = [l + vt for l, vt in zip(all_latencies, all_verify_times)]
        ghost_violations = sum(1 for r in self.regions.values() for v in r if not v.ghost_valid)
        coverage = sum(1 for r in self.regions.values() for v in r if v.loopseal_submitted) / (len(self.regions) * self.n_validators_per_region)

        return {
            "latency_diffusion_avg_ms": float(sum(all_latencies) / len(all_latencies) if all_latencies else 0.0),
            "latency_diffusion_max_ms": float(max(all_latencies) if all_latencies else 0.0),
            "latency_verification_avg_ms": float(sum(all_verify_times) / len(all_verify_times) if all_verify_times else 0.0),
            "latency_total_avg_ms": float(sum(total_latencies) / len(total_latencies) if total_latencies else 0.0),
            "latency_total_max_ms": float(max(total_latencies) if total_latencies else 0.0),
            "cross_region_sync_jitter_avg_ms": float(sum(all_sync_jitters) / len(all_sync_jitters) if all_sync_jitters else 0.0),
            "ghost_violations": ghost_violations,
            "coverage_ratio": coverage,
            "validators_total": len(self.regions) * self.n_validators_per_region,
            "validators_ghost_valid": sum(1 for r in self.regions.values() for v in r if v.ghost_valid),
            "validators_loopseal_registered": sum(1 for r in self.regions.values() for v in r if v.loopseal_submitted),
            "regions_active": len(self.regions),
        }

    def calculate_phi_c_global(self, metrics: Dict, integration: Dict) -> float:
        """Calcular Φ_C global da execução multi-região + integração pública."""
        # Componentes de Φ_C
        latency_score = max(0, 1.0 - (metrics["latency_total_avg_ms"] / 100))
        ghost_score = 1.0 if metrics["ghost_violations"] == 0 else 0.5
        coverage_score = metrics["coverage_ratio"]
        integration_score = integration["avg_fidelity"]  # Fidelidade da integração pública
        multi_region_score = 0.95 if metrics["regions_active"] >= 4 else 0.7

        # Ponderação ajustada para rede global
        phi_c = (
            latency_score * 0.25 +
            ghost_score * 0.30 +
            coverage_score * 0.15 +
            integration_score * 0.20 +
            multi_region_score * 0.10
        )

        return max(GHOST, min(GAP_SOVEREIGN, phi_c))

    def generate_canonical_seal_global(self, metrics: Dict, integration: Dict, phi_c: float) -> Dict:
        """Gerar selo canônico SHA3-256 da execução global."""
        hasher = hashlib.sha3_256()

        # Identidade da execução global
        hasher.update(b'Substrate_376_Global_Alert_Network_Public_Integration')
        hasher.update(str(phi_c).encode())
        hasher.update(str(metrics["ghost_violations"]).encode())
        hasher.update(str(metrics["coverage_ratio"]).encode())
        hasher.update(str(integration["avg_fidelity"]).encode())

        # Métricas chave
        hasher.update(struct.pack('<d', metrics["latency_total_avg_ms"]))
        hasher.update(struct.pack('<d', metrics["cross_region_sync_jitter_avg_ms"]))

        # Alert info por região
        for region_code, alert in self.alerts.items():
            hasher.update(alert.alert_id.encode())
            hasher.update(region_code.encode())

        # Timestamp global
        hasher.update(datetime.now(timezone.utc).isoformat().encode())

        seal_hash = hasher.hexdigest()

        return {
            "substrate_id": "376-GLOBAL-ALERT",
            "substrate_name": "Global_Alert_Network_Public_System_Integration",
            "phi_c": phi_c,
            "metrics_summary": {
                "latency_total_avg_ms": metrics["latency_total_avg_ms"],
                "ghost_violations": metrics["ghost_violations"],
                "coverage_ratio": metrics["coverage_ratio"],
                "integration_fidelity": integration["avg_fidelity"],
                "regions_active": metrics["regions_active"],
            },
            "seal_hash": seal_hash,
            "canonical_constants": {
                "GHOST": GHOST,
                "LOOPSEAL": LOOPSEAL,
                "GAP_SOVEREIGN": GAP_SOVEREIGN,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "CANONIZED" if phi_c > GHOST and metrics["ghost_violations"] == 0 and integration["avg_fidelity"] >= 0.95 else "QUARANTINE"
        }

    def execute_full_simulation(self) -> Dict:
        """Executar simulação completa da rede global de alertas."""
        print("🌐🚨 Inicializando Substrato 376: Rede Global de Alertas + Integração Pública")
        print(f"   → {len(REGIONAL_CONFIGS)} regiões: {', '.join(REGIONAL_CONFIGS.keys())}")
        print(f"   → {self.n_validators_per_region} validadores por região = {len(REGIONAL_CONFIGS) * self.n_validators_per_region} total")
        print()

        # FASE 1: Gerar alertas canônicos por região
        print("📝 FASE 1: Geração de Alertas Canônicos Multi-Região")
        alerts = self.generate_canonical_alerts()
        for region_code, alert in alerts.items():
            config = REGIONAL_CONFIGS[region_code]
            print(f"   → {region_code} ({config.city}): {alert.alert_id} | {alert.system.value}")
        print()

        # FASE 2: Testar integração com sistemas públicos
        print("🔗 FASE 2: Integração com Sistemas Públicos de Alerta")
        integration = self.test_public_alert_integration()
        for system, result in integration["by_system"].items():
            status = "✅" if result["fidelity"] >= 0.95 else "⚠️"
            print(f"   {status} {system}: ingest={'OK' if result['ingest_ok'] else 'FAIL'}, "
                  f"export={'OK' if result['export_ok'] else 'FAIL'}, fidelity={result['fidelity']:.3f}")
        print(f"   → Fidelidade canônica média: {integration['avg_fidelity']:.3f}")
        print()

        # FASE 3-4: Sincronização e Difusão Regional Simultânea
        print("📡 FASE 3-4: Sincronização Cross-Região e Difusão Simultânea")
        broadcast = self.broadcast_regional_alerts(alerts)
        for region_code, results in broadcast["regions"].items():
            config = REGIONAL_CONFIGS[region_code]
            print(f"   → {region_code} ({config.city}): "
                  f"{results['validators_reached']}/{self.n_validators_per_region} reached, "
                  f"latency={sum(results['latencies_ms'])/len(results['latencies_ms']):.2f} ms")
        print(f"   → Sincronização cross-região jitter médio: "
              f"{sum([j for r in broadcast['regions'].values() for j in r['cross_region_sync_ns']]) / (len(broadcast['regions']) * self.n_validators_per_region) / 1e6:.3f} ms")
        print()

        # FASE 5: Verificação Ghost Global
        print("🔐 FASE 5: Verificação Ghost Global (Dilithium3 + Merkle)")
        ghost = self.verify_ghost_global(alerts)
        print(f"   → Assinaturas verificadas: {ghost['signature_verified_count']}/{ghost['total_validators']}")
        print(f"   → Merkle roots verificados: {ghost['merkle_verified_count']}/{ghost['total_validators']}")
        print(f"   → Ghost válidos: {ghost['ghost_valid_count']}/{ghost['total_validators']}")
        print(f"   → Tempo verificação médio: {sum(ghost['verification_times_ms'])/len(ghost['verification_times_ms']):.2f} ms")
        for region_code, rg in ghost["by_region"].items():
            print(f"     • {region_code}: {rg['ghost_valid']}/{self.n_validators_per_region} válidos")
        print()

        # FASE 6: Registo Loopseal Global
        print("⛓️ FASE 6: Registo na TemporalChain via Loopseal (Global)")
        loopseal = self.register_loopseal_global()
        print(f"   → Transações submetidas: {loopseal['transactions_submitted']}/{ghost['total_validators']}")
        print(f"   → Eventos registados: {loopseal['events_registered']}")
        print(f"   → Tempo submissão médio: {sum(loopseal['submission_times_ms'])/len(loopseal['submission_times_ms']):.2f} ms")
        print()

        # FASE 7-8: Métricas Globais e Selo Canônico
        print("📊 FASE 7-8: Métricas Globais e Selo Canônico")
        metrics = self.compute_global_metrics()
        phi_c = self.calculate_phi_c_global(metrics, integration)
        seal = self.generate_canonical_seal_global(metrics, integration, phi_c)

        print(f"   → Latência difusão média: {metrics['latency_diffusion_avg_ms']:.2f} ms")
        print(f"   → Latência verificação média: {metrics['latency_verification_avg_ms']:.2f} ms")
        print(f"   → Latência total média: {metrics['latency_total_avg_ms']:.2f} ms")
        print(f"   → Jitter sincronização cross-região: {metrics['cross_region_sync_jitter_avg_ms']:.3f} ms")
        print(f"   → Violações Ghost: {metrics['ghost_violations']}")
        print(f"   → Cobertura global: {metrics['coverage_ratio']*100:.1f}%")
        print(f"   → Fidelidade integração pública: {integration['avg_fidelity']:.3f}")
        print(f"   → Φ_C da execução global: {phi_c:.4f}")
        print(f"   → Selo: {seal['seal_hash'][:32]}...")
        print(f"   → Status: {seal['status']}")
        print()

        return {
            "alerts": alerts,
            "integration": integration,
            "broadcast": broadcast,
            "ghost": ghost,
            "loopseal": loopseal,
            "metrics": metrics,
            "phi_c": phi_c,
            "seal": seal,
        }

if __name__ == '__main__':
    simulation = GlobalAlertNetworkSimulation(n_validators_per_region=59)
    results = simulation.execute_full_simulation()

    print("═"*70)
    print("CANONIZAÇÃO SUBSTRATO 376 — RESUMO EXECUTIVO")
    print("═"*70)
    print(json.dumps({
        "substrato": "376-GLOBAL-ALERT",
        "nome": "Global_Alert_Network_Public_System_Integration",
        "phi_c": results["phi_c"],
        "status": results["seal"]["status"],
        "selo": results["seal"]["seal_hash"],
        "regioes": results["metrics"]["regions_active"],
        "validadores_totais": results["metrics"]["validators_total"],
        "ghost_validos": results["metrics"]["validators_ghost_valid"],
        "cobertura_global": f"{results['metrics']['coverage_ratio']*100:.1f}%",
        "latencia_total_media_ms": results["metrics"]["latency_total_avg_ms"],
        "jitter_sincronizacao_ms": results["metrics"]["cross_region_sync_jitter_avg_ms"],
        "fidelidade_integracao": results["integration"]["avg_fidelity"],
        "violacoes_ghost": results["metrics"]["ghost_violations"],
        "sistemas_publicos_integrados": results["integration"]["systems_tested"],
        "timestamp": results["seal"]["timestamp"]
    }, indent=2, ensure_ascii=False))
    print("═"*70)
