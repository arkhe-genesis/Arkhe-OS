#!/usr/bin/env python3
"""
Substrato 183-B: Configuração de Expansão SCADA para Múltiplas Indústrias
Define parâmetros específicos para energia, água, gás e manufatura com
validação Φ_C adaptativa e guardrails por domínio industrial.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum, auto
import hashlib, time

class IndustryType(Enum):
    """Tipos de indústrias para expansão do piloto SCADA."""
    ENERGY = "energy"              # Geração, transmissão, distribuição elétrica
    WATER = "water"                # Tratamento, distribuição, saneamento
    GAS = "gas"                    # Distribuição de gás natural, LNG
    MANUFACTURING = "manufacturing"  # Linhas de produção, automação industrial

@dataclass
class IndustrySCADAConfig:
    """Configuração específica por tipo de indústria."""
    industry: IndustryType
    critical_parameters: Dict[str, Dict]  # parâmetro → {min, max, unit, alert_threshold}
    safety_protocols: List[str]  # Protocolos de segurança obrigatórios
    phi_c_thresholds: Dict[str, float]  # operation → min Φ_C
    integration_endpoints: Dict[str, str]  # sistema → endpoint
    regulatory_compliance: List[str]  # Normas aplicáveis (ex: ANEEL, ANA, ANP)

    # Parâmetros de piloto
    polling_interval_sec: float = 1.0
    test_duration_hours: int = 24
    alert_channels: List[str] = field(default_factory=lambda: ["ops", "safety", "regulatory"])

# Configurações pré-definidas por indústria
INDUSTRY_CONFIGS = {
    IndustryType.ENERGY: IndustrySCADAConfig(
        industry=IndustryType.ENERGY,
        critical_parameters={
            "voltage_kv": {"min": 13.8, "max": 500, "unit": "kV", "alert_threshold": 0.05},
            "frequency_hz": {"min": 59.5, "max": 60.5, "unit": "Hz", "alert_threshold": 0.02},
            "load_mw": {"min": 0, "max": 2000, "unit": "MW", "alert_threshold": 0.15},
            "transformer_temp_c": {"min": -10, "max": 95, "unit": "°C", "alert_threshold": 0.10},
        },
        safety_protocols=[
            "IEEE_1547_interconnection",
            "NERC_CIP_cybersecurity",
            "IEC_61850_substation_automation",
        ],
        phi_c_thresholds={
            "normal_operation": 0.95,
            "emergency_response": 0.99,
            "load_shedding": 0.999,
        },
        integration_endpoints={
            "ems": "https://ems.energy.arkhe.internal/api",
            "scada_master": "modbus+tcp://scada.energy.arkhe.internal:502",
            "protection_relays": "iec61850://relays.energy.arkhe.internal:102",
        },
        regulatory_compliance=["ANEEL_RES_1000_2021", "ONS_PROC_001_2023"],
    ),

    IndustryType.WATER: IndustrySCADAConfig(
        industry=IndustryType.WATER,
        critical_parameters={
            "pressure_bar": {"min": 0.5, "max": 12, "unit": "bar", "alert_threshold": 0.08},
            "flow_rate_m3h": {"min": 0, "max": 5000, "unit": "m³/h", "alert_threshold": 0.12},
            "turbidity_ntu": {"min": 0, "max": 5, "unit": "NTU", "alert_threshold": 0.20},
            "chlorine_residual_mgl": {"min": 0.2, "max": 2.0, "unit": "mg/L", "alert_threshold": 0.15},
        },
        safety_protocols=[
            "AWWA_C651_disinfection",
            "ISO_24510_water_services",
            "IEC_62443_industrial_security",
        ],
        phi_c_thresholds={
            "normal_operation": 0.95,
            "contamination_alert": 0.99,
            "emergency_shutdown": 0.999,
        },
        integration_endpoints={
            "water_management": "https://wms.water.arkhe.internal/api",
            "plc_network": "modbus+tcp://plc.water.arkhe.internal:502",
            "quality_sensors": "mqtt://sensors.water.arkhe.internal:1883",
        },
        regulatory_compliance=["ANA_RES_123_2022", "PORTARIA_MS_888_2021"],
    ),

    IndustryType.GAS: IndustrySCADAConfig(
        industry=IndustryType.GAS,
        critical_parameters={
            "pressure_psig": {"min": 50, "max": 1200, "unit": "psig", "alert_threshold": 0.05},
            "flow_rate_mmscfd": {"min": 0, "max": 500, "unit": "MMSCFD", "alert_threshold": 0.10},
            "odorant_ppm": {"min": 0.5, "max": 5, "unit": "ppm", "alert_threshold": 0.25},
            "leak_detection": {"min": 0, "max": 1, "unit": "boolean", "alert_threshold": 0.01},  # Any detection = alert
        },
        safety_protocols=[
            "API_1160_pipeline_integrity",
            "PHMSA_49_CFR_192_regulations",
            "IEC_61511_functional_safety",
        ],
        phi_c_thresholds={
            "normal_operation": 0.95,
            "pressure_anomaly": 0.99,
            "leak_emergency": 0.9999,  # Máxima coerência para resposta a vazamentos
        },
        integration_endpoints={
            "gas_management": "https://gms.gas.arkhe.internal/api",
            "pipeline_scada": "dnp3+tcp://pipeline.gas.arkhe.internal:20000",
            "leak_sensors": "mqtt://leak.gas.arkhe.internal:1883",
        },
        regulatory_compliance=["ANP_RES_800_2020", "NBR_15844_gas_distribution"],
    ),

    IndustryType.MANUFACTURING: IndustrySCADAConfig(
        industry=IndustryType.MANUFACTURING,
        critical_parameters={
            "production_rate_units_h": {"min": 0, "max": 10000, "unit": "units/h", "alert_threshold": 0.15},
            "machine_temp_c": {"min": 20, "max": 85, "unit": "°C", "alert_threshold": 0.08},
            "vibration_mm_s": {"min": 0, "max": 25, "unit": "mm/s", "alert_threshold": 0.20},
            "quality_defect_rate": {"min": 0, "max": 0.05, "unit": "ratio", "alert_threshold": 0.30},
        },
        safety_protocols=[
            "ISO_13849_machine_safety",
            "IEC_62061_functional_safety",
            "ISA_95_enterprise_control",
        ],
        phi_c_thresholds={
            "normal_operation": 0.95,
            "quality_deviation": 0.97,
            "safety_stop": 0.999,
        },
        integration_endpoints={
            "mes_system": "https://mes.manufacturing.arkhe.internal/api",
            "plc_line": "profinet+tcp://line.manufacturing.arkhe.internal:34962",
            "quality_sensors": "opcua+tcp://quality.manufacturing.arkhe.internal:4840",
        },
        regulatory_compliance=["NR_12_machine_safety", "ISO_9001_quality_management"],
    ),
}

def generate_industry_pilot_config(
    industry: IndustryType,
    facility_id: str,
    rtu_endpoints: List[str],
) -> Dict:
    """Gera configuração completa de piloto para uma indústria específica."""
    config = INDUSTRY_CONFIGS[industry]

    return {
        "pilot_id": hashlib.sha3_256(
            f"{industry.value}:{facility_id}:{time.time()}".encode()
        ).hexdigest()[:12],
        "industry": industry.value,
        "facility_id": facility_id,
        "rtu_endpoints": rtu_endpoints,
        "critical_parameters": config.critical_parameters,
        "safety_protocols": config.safety_protocols,
        "phi_c_thresholds": config.phi_c_thresholds,
        "integration_endpoints": config.integration_endpoints,
        "regulatory_compliance": config.regulatory_compliance,
        "polling_interval_sec": config.polling_interval_sec,
        "test_duration_hours": config.test_duration_hours,
        "alert_channels": config.alert_channels,
        "temporal_chain_enabled": True,
        "guardian_integration": True,
        "pqc_signing_enabled": True,
    }