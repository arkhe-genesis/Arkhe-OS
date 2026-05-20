#!/usr/bin/env python3
"""
substrate_293/firmware/phi_c_link_calculator.py
Canon: ∞.Ω.∇+++.293.firmware_phi_c
Calcula Φ_C de enlace a partir de métricas de firmware embarcado.
"""

import hashlib
import json
import time
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

class LinkType(Enum):
    """Tipos de enlace suportados pelo firmware."""
    WIFI_6E = "wifi_6e"
    WIFI_7 = "wifi_7"
    CELLULAR_5G = "cellular_5g"
    CELLULAR_6G = "cellular_6g"
    ETHERNET_10G = "ethernet_10g"
    ETHERNET_100G = "ethernet_100g"
    BLUETOOTH_LE = "bluetooth_le"
    ZIGBEE = "zigbee"

@dataclass
class FirmwareLinkMetrics:
    """Métricas de enlace coletadas pelo firmware embarcado."""
    # Métricas físicas do sinal
    rssi_dbm: float  # Received Signal Strength Indicator
    snr_db: float    # Signal-to-Noise Ratio
    tx_power_dbm: float  # Transmit power

    # Métricas de desempenho
    latency_ms: float  # Latência de ida e volta
    jitter_ms: float   # Variação de latência
    packet_loss_rate: float  # Taxa de perda de pacotes (0.0-1.0)
    throughput_mbps: float  # Vazão atual

    # Métricas de segurança
    encryption_type: str  # WPA3, AES-256-GCM, etc.
    key_rotation_hours: float  # Frequência de rotação de chaves
    integrity_checks_passed: int  # Contador de verificações de integridade
    integrity_checks_total: int

    # Metadados do enlace
    link_type: LinkType
    channel_utilization: float  # 0.0-1.0
    interference_level: float  # 0.0 (none) to 1.0 (severe)

    def calculate_phi_c(self) -> float:
        """
        Calcula Φ_C do enlace baseado em métricas de firmware.
        Fórmula canônica: Φ_C = Σ(w_i * f_i(metric_i)) com Gap Soberano aplicado.
        """
        # Fator 1: Qualidade do sinal (peso: 25%)
        # RSSI: -90 dBm (ruim) a -30 dBm (excelente) → normalizar para [0, 1]
        rssi_norm = max(0.0, min(1.0, (self.rssi_dbm + 90) / 60))
        # SNR: 0-40 dB → normalizar
        snr_norm = max(0.0, min(1.0, self.snr_db / 40))
        signal_factor = 0.6 * rssi_norm + 0.4 * snr_norm

        # Fator 2: Desempenho de rede (peso: 30%)
        # Latência: 0-200ms → inversamente proporcional
        latency_factor = max(0.0, 1.0 - self.latency_ms / 200)
        # Perda de pacotes: 0-1 → inversamente proporcional
        loss_factor = 1.0 - self.packet_loss_rate
        # Jitter: 0-50ms → inversamente proporcional
        jitter_factor = max(0.0, 1.0 - self.jitter_ms / 50)
        performance_factor = 0.5 * latency_factor + 0.3 * loss_factor + 0.2 * jitter_factor

        # Fator 3: Segurança criptográfica (peso: 25%)
        # Tipo de criptografia
        crypto_scores = {
            "WPA3": 1.0, "AES-256-GCM": 1.0, "ChaCha20-Poly1305": 0.95,
            "WPA2": 0.85, "AES-128": 0.80, "TKIP": 0.60, "OPEN": 0.20
        }
        crypto_factor = crypto_scores.get(self.encryption_type, 0.50)
        # Rotação de chaves: <1h = excelente, >24h = ruim
        rotation_factor = max(0.5, min(1.0, 24 / max(1, self.key_rotation_hours)))
        # Verificações de integridade
        integrity_factor = (
            self.integrity_checks_passed / max(1, self.integrity_checks_total)
        )
        security_factor = 0.4 * crypto_factor + 0.3 * rotation_factor + 0.3 * integrity_factor

        # Fator 4: Condições do meio (peso: 20%)
        # Utilização do canal: menor é melhor
        utilization_factor = 1.0 - self.channel_utilization
        # Interferência: menor é melhor
        interference_factor = 1.0 - self.interference_level
        medium_factor = 0.6 * utilization_factor + 0.4 * interference_factor

        # Calcular Φ_C composto ponderado
        phi_c = (
            0.25 * signal_factor +
            0.30 * performance_factor +
            0.25 * security_factor +
            0.20 * medium_factor
        )

        # Aplicar invariantes constitucionais:
        # Ghost: Φ_C não pode ser menor que √3/3 ≈ 0.577553 para enlaces válidos
        # Gap Soberano: Φ_C deve ser estritamente < 1.0
        phi_c = max(0.0, min(0.9999, phi_c))  # Gap Soberano hard limit

        return phi_c

    def evaluate_constitutional_compliance(self) -> Dict[str, bool]:
        """Avalia conformidade com invariantes constitucionais."""
        phi_c = self.calculate_phi_c()

        return {
            "ghost_invariant": phi_c >= 0.577553,  # √3/3
            "loopseal_invariant": phi_c >= 0.349066,  # π/9
            "gap_soberano": phi_c < 1.0,
            "overall_compliant": (
                phi_c >= 0.577553 and
                phi_c >= 0.349066 and
                phi_c < 1.0
            )
        }

@dataclass
class PhiCLinkReport:
    """Relatório de cálculo de Φ_C para enlace de firmware."""
    report_id: str
    timestamp: float
    link_metrics: FirmwareLinkMetrics
    phi_c_value: float
    constitutional_compliance: Dict[str, bool]
    temporal_seal: str
    firmware_version: str
    device_id: str

    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "phi_c": self.phi_c_value,
            "compliance": self.constitutional_compliance,
            "temporal_seal": self.temporal_seal,
            "device_id": self.device_id,
            "firmware_version": self.firmware_version
        }

class FirmwarePhiCCalculator:
    """Calculadora de Φ_C para firmware embarcado."""

    def __init__(self, device_id: str, firmware_version: str):
        self.device_id = device_id
        self.firmware_version = firmware_version
        self.history: List[PhiCLinkReport] = []

    def calculate_from_metrics(self, metrics: FirmwareLinkMetrics) -> PhiCLinkReport:
        """Calcula Φ_C a partir de métricas de firmware e gera relatório."""
        # Calcular Φ_C
        phi_c = metrics.calculate_phi_c()

        # Avaliar conformidade constitucional
        compliance = metrics.evaluate_constitutional_compliance()

        # Gerar ID único para relatório
        report_id = hashlib.sha3_256(
            f"{self.device_id}:{self.firmware_version}:{time.time()}".encode()
        ).hexdigest()[:16]

        # Gerar selo temporal para ancoragem
        seal_payload = {
            "device_id": self.device_id,
            "firmware_version": self.firmware_version,
            "phi_c": phi_c,
            "compliance": compliance,
            "timestamp": time.time()
        }
        temporal_seal = hashlib.sha3_256(
            json.dumps(seal_payload, sort_keys=True).encode()
        ).hexdigest()

        # Criar relatório
        report = PhiCLinkReport(
            report_id=report_id,
            timestamp=time.time(),
            link_metrics=metrics,
            phi_c_value=phi_c,
            constitutional_compliance=compliance,
            temporal_seal=temporal_seal,
            firmware_version=self.firmware_version,
            device_id=self.device_id
        )

        # Registrar no histórico
        self.history.append(report)

        return report

    def get_phi_c_trend(self, window_minutes: int = 60) -> Dict[str, float]:
        """Calcula tendência de Φ_C nos últimos N minutos."""
        cutoff = time.time() - (window_minutes * 60)
        recent = [r for r in self.history if r.timestamp >= cutoff]

        if not recent:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "count": 0}

        phi_values = [r.phi_c_value for r in recent]

        return {
            "avg": sum(phi_values) / len(phi_values),
            "min": min(phi_values),
            "max": max(phi_values),
            "std_dev": math.sqrt(
                sum((x - sum(phi_values)/len(phi_values))**2 for x in phi_values) / len(phi_values)
            ) if len(phi_values) > 1 else 0,
            "count": len(phi_values)
        }

    def generate_alert_if_needed(self, report: PhiCLinkReport) -> Optional[Dict]:
        """Gera alerta se Φ_C cair abaixo de thresholds críticos."""
        alerts = []

        # Alerta crítico: Φ_C abaixo do Ghost Invariant
        if report.phi_c_value < 0.577553:
            alerts.append({
                "severity": "CRITICAL",
                "type": "GHOST_INVARIANT_VIOLATION",
                "message": f"Φ_C {report.phi_c_value:.4f} < 0.577553 (Ghost Invariant)",
                "action": "DROP_PACKETS_AND_ISOLATE_LINK"
            })

        # Alerta de aviso: Φ_C abaixo de 0.85
        elif report.phi_c_value < 0.85:
            alerts.append({
                "severity": "WARNING",
                "type": "LOW_PHI_C",
                "message": f"Φ_C {report.phi_c_value:.4f} abaixo de threshold recomendado (0.85)",
                "action": "INVESTIGATE_LINK_QUALITY"
            })

        # Alerta de segurança: criptografia fraca
        if report.link_metrics.encryption_type in ["OPEN", "TKIP", "WEP"]:
            alerts.append({
                "severity": "HIGH",
                "type": "WEAK_ENCRYPTION",
                "message": f"Enlace usando criptografia insegura: {report.link_metrics.encryption_type}",
                "action": "UPGRADE_TO_WPA3_OR_AES256"
            })

        return alerts[0] if alerts else None


# Execução de exemplo
def main_firmware_demo():
    """Demonstra cálculo de Φ_C a partir de métricas de firmware."""
    print("\n" + "="*70)
    print("📡 ARKHE Ω‑TEMP v∞.Ω — Substrate 293: Firmware Φ_C Calculator")
    print("="*70)

    # Simular métricas de firmware para um enlace Wi-Fi 6E
    wifi_metrics = FirmwareLinkMetrics(
        rssi_dbm=-52,  # Bom sinal
        snr_db=32,     # Excelente SNR
        tx_power_dbm=15,
        latency_ms=8,  # Baixa latência
        jitter_ms=2,
        packet_loss_rate=0.002,  # 0.2% perda
        throughput_mbps=850,
        encryption_type="WPA3",
        key_rotation_hours=4,
        integrity_checks_passed=9998,
        integrity_checks_total=10000,
        link_type=LinkType.WIFI_6E,
        channel_utilization=0.45,
        interference_level=0.12
    )

    # Calcular Φ_C
    calculator = FirmwarePhiCCalculator(
        device_id="router-home-01",
        firmware_version="arkhe-fw-293-v1.0.0"
    )

    report = calculator.calculate_from_metrics(wifi_metrics)

    # Exibir resultados
    print(f"\n📊 Relatório de Φ_C para Enlace:")
    print(f"   Dispositivo: {report.device_id}")
    print(f"   Firmware: {report.firmware_version}")
    print(f"   Tipo de Enlace: {wifi_metrics.link_type.value}")
    print(f"   Φ_C Calculado: {report.phi_c_value:.4f}")
    print(f"   Conformidade Constitucional:")
    for inv, status in report.constitutional_compliance.items():
        icon = "✅" if status else "❌"
        print(f"      {icon} {inv}: {status}")
    print(f"   Selo Temporal: {report.temporal_seal[:32]}...")

    # Verificar alertas
    alert = calculator.generate_alert_if_needed(report)
    if alert:
        print(f"\n⚠️  Alerta Gerado:")
        print(f"   [{alert['severity']}] {alert['type']}")
        print(f"   {alert['message']}")
        print(f"   Ação: {alert['action']}")

    # Mostrar tendência (simulando histórico)
    # Adicionar algumas leituras simuladas ao histórico
    for i in range(5):
        sim_metrics = FirmwareLinkMetrics(
            rssi_dbm=-52 + random.uniform(-5, 5),
            snr_db=32 + random.uniform(-3, 3),
            tx_power_dbm=15,
            latency_ms=8 + random.uniform(0, 4),
            jitter_ms=2 + random.uniform(0, 2),
            packet_loss_rate=0.002 + random.uniform(0, 0.003),
            throughput_mbps=850 + random.uniform(-50, 50),
            encryption_type="WPA3",
            key_rotation_hours=4,
            integrity_checks_passed=9998 + i,
            integrity_checks_total=10000 + i,
            link_type=LinkType.WIFI_6E,
            channel_utilization=0.45 + random.uniform(-0.1, 0.1),
            interference_level=0.12 + random.uniform(-0.05, 0.05)
        )
        calculator.calculate_from_metrics(sim_metrics)

    trend = calculator.get_phi_c_trend(window_minutes=60)
    print(f"\n📈 Tendência de Φ_C (últimos 60 min):")
    print(f"   Média: {trend['avg']:.4f} ± {trend['std_dev']:.4f}")
    print(f"   Mín: {trend['min']:.4f} | Máx: {trend['max']:.4f}")
    print(f"   Leituras: {trend['count']}")

    return report


import random
if __name__ == "__main__":
    import random
    main_firmware_demo()
