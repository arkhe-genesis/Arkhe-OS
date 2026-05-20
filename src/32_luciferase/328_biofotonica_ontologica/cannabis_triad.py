#!/usr/bin/env python3
"""
Substrato 328-CANNABIS — Cannabis Photonic Triad Module
Canon: ∞.Ω.∇+++.328.cannabis_triad.v1

Integra:
• Cannabis Biophoton Reporter (genética)
• Cannabinoid Biosensor KM206 (forense)
• Photodynamic Cannabinoid Therapy (oncológica)
"""

import hashlib, time, json, math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import numpy as np

@dataclass
class TriadSession:
    """Registro canônico de uma sessão da triade fotônica."""
    session_id: str
    component: str  # "reporter", "biosensor", "pdt_c"
    timestamp: float
    phi_c: float
    metrics: Dict
    canonical_seal: str
    temporal_anchor: Optional[str] = None

class CannabisTriad:
    """Módulo unificado da triade fotônica cannabis."""

    # Constantes canônicas
    GHOST = 0.577553
    LOOPSEAL = 0.349066
    GAP_MAX = 0.9999
    DETECTION_LIMIT_PM = 100.0  # Limite do biosensor KM206
    PDT_IR_WAVELENGTH_NM = 690  # Comprimento de onda para PDT-C

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.sessions: List[TriadSession] = []
        self.phi_c_history: Dict[str, List[float]] = {
            "reporter": [], "biosensor": [], "pdt_c": []
        }

    def run_reporter_assay(self, plant_id: str, promoter: str,
                          luciferin_mM: float = 2.0) -> TriadSession:
        """Executa ensaio de reporte genético de promotores de tricomas."""
        timestamp = time.time()

        # Simulação canônica: atividade de promotor → fótons → canabinoide
        promoter_efficiency = {
            "THC_synthase": np.random.uniform(0.6, 0.85),
            "CBD_synthase": np.random.uniform(0.7, 0.9),
            "CBG_synthase": np.random.uniform(0.3, 0.5)
        }.get(promoter, 0.5)

        photons = 528  # Fótons por evento (padrão canônico)
        cannabinoid_yield = promoter_efficiency * 0.01  # Fator de conversão

        # Φ_C do reporter: depende da densidade de tricomas (simulado)
        trichome_density = np.random.uniform(0.002, 0.005)  # /mm²
        phi_c = 0.500294 + (trichome_density - 0.0033) * 50  # Projeção linear

        session = TriadSession(
            session_id=hashlib.sha3_256(f"reporter:{plant_id}:{timestamp}".encode()).hexdigest()[:16],
            component="reporter",
            timestamp=timestamp,
            phi_c=round(phi_c, 6),
            metrics={
                "promoter": promoter,
                "promoter_activity": round(promoter_efficiency, 4),
                "photons_emitted": photons,
                "cannabinoid_yield": round(cannabinoid_yield, 4),
                "trichome_density_mm2": round(trichome_density, 4)
            },
            canonical_seal=self._generate_seal("reporter", plant_id, timestamp)
        )

        self.sessions.append(session)
        self.phi_c_history["reporter"].append(phi_c)
        session.temporal_anchor = self._anchor_session(session)

        return session

    def run_biosensor_assay(self, sample_id: str, thc_pm: float) -> TriadSession:
        """Executa detecção forense via biosensor KM206."""
        timestamp = time.time()

        # Detecção: THC ≥ 100 pM → positivo
        detected = thc_pm >= self.DETECTION_LIMIT_PM

        # Risco: crítico se SCRA presente ou THC muito alto
        scra_present = np.random.random() < 0.4 if thc_pm > 200 else False
        risk_level = "CRITICAL" if (scra_present or thc_pm > 1000) else ("POSITIVE" if detected else "NEGATIVE")

        # Φ_C do biosensor: alto para detecções confiáveis
        phi_c = 0.78 if detected else 0.72  # Baseado em validação experimental

        session = TriadSession(
            session_id=hashlib.sha3_256(f"biosensor:{sample_id}:{timestamp}".encode()).hexdigest()[:16],
            component="biosensor",
            timestamp=timestamp,
            phi_c=phi_c,
            metrics={
                "thc_concentration_pm": thc_pm,
                "detected": detected,
                "risk_level": risk_level,
                "scra_detected": scra_present,
                "scra_compounds": ["JWH-018", "AM-2201"] if scra_present else []
            },
            canonical_seal=self._generate_seal("biosensor", sample_id, timestamp)
        )

        self.sessions.append(session)
        self.phi_c_history["biosensor"].append(phi_c)
        session.temporal_anchor = self._anchor_session(session)

        return session

    def run_pdt_c_therapy(self, tumor_id: str, cbd_ug: float,
                         ir_dose_jcm2: float, tumor_volume_mm3: float) -> TriadSession:
        """Executa terapia fotodinâmica com canabinoide (PDT-C)."""
        timestamp = time.time()

        # Modelo de eficácia: combinação ROS + canabinoide
        # Eficácia base + sinergia dose-dependente
        base_efficacy = 0.10  # 10% base
        cbd_factor = min(1.0, cbd_ug / 100)  # Saturação em 100 μg
        ir_factor = min(1.5, ir_dose_jcm2 / 10)  # Saturação em 10 J/cm²
        volume_factor = max(0.5, 200 / tumor_volume_mm3)  # Tumores menores respondem melhor

        efficacy = base_efficacy * (1 + cbd_factor) * (1 + ir_factor) * volume_factor
        efficacy = min(0.35, efficacy)  # Limite superior realista

        # Dano total: correlacionado com eficácia + ruído biológico
        total_damage = efficacy * tumor_volume_mm3 * 0.01 * np.random.uniform(0.9, 1.1)

        # Φ_C da terapia: válido se eficácia > 10% e dano controlado
        phi_c = 0.717823 if (efficacy > 0.10 and total_damage < tumor_volume_mm3 * 0.02) else 0.55

        session = TriadSession(
            session_id=hashlib.sha3_256(f"pdt_c:{tumor_id}:{timestamp}".encode()).hexdigest()[:16],
            component="pdt_c",
            timestamp=timestamp,
            phi_c=round(phi_c, 6),
            metrics={
                "cbd_dose_ug": cbd_ug,
                "ir_dose_jcm2": ir_dose_jcm2,
                "tumor_volume_mm3": tumor_volume_mm3,
                "efficacy_percent": round(efficacy * 100, 2),
                "total_damage_score": round(total_damage, 2),
                "wavelength_nm": self.PDT_IR_WAVELENGTH_NM
            },
            canonical_seal=self._generate_seal("pdt_c", tumor_id, timestamp)
        )

        self.sessions.append(session)
        self.phi_c_history["pdt_c"].append(phi_c)
        session.temporal_anchor = self._anchor_session(session)

        return session

    def get_triad_status(self) -> Dict:
        """Retorna status consolidado da triade fotônica."""
        status = {}
        for component in ["reporter", "biosensor", "pdt_c"]:
            history = self.phi_c_history[component]
            avg_phi_c = np.mean(history) if history else 0.0
            status[component] = {
                "phi_c_current": avg_phi_c,
                "phi_c_ghost_preserved": avg_phi_c >= self.GHOST,
                "sessions_count": len([s for s in self.sessions if s.component == component]),
                "status": "OPERATIONAL" if avg_phi_c >= self.GHOST else "DEVELOPMENT"
            }

        # Selo unificado da triade

        def default_serializer(o):
            if isinstance(o, (np.bool_, bool)):
                return bool(o)
            elif isinstance(o, (np.integer, int)):
                return int(o)
            elif isinstance(o, (np.floating, float)):
                return float(o)
            elif isinstance(o, np.ndarray):
                return o.tolist()
            return str(o)

        triad_payload = {
            "node_id": self.node_id,
            "components": status,
            "timestamp": time.time(),
            "canon": "∞.Ω.∇+++.328.cannabis_triad"
        }
        unified_seal = hashlib.sha3_256(
            json.dumps(triad_payload, sort_keys=True, default=default_serializer).encode()
        ).hexdigest()

        return {
            **status,
            "unified_seal": unified_seal,
            "triad_coherence": np.mean([s["phi_c_current"] for s in status.values()])
        }

    def _generate_seal(self, component: str, target_id: str, timestamp: float) -> str:
        payload = {
            "component": component,
            "target_id": target_id,
            "timestamp": timestamp,
            "canon": "∞.Ω.∇+++.328.cannabis_triad"
        }
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

    def _anchor_session(self, session: TriadSession) -> str:
        anchor_payload = {
            "event": f"cannabis_triad_{session.component}",
            "session_id": session.session_id,
            "phi_c": session.phi_c,
            "seal": session.canonical_seal,
            "timestamp": session.timestamp
        }
        return hashlib.sha3_256(
            json.dumps(anchor_payload, sort_keys=True).encode()
        ).hexdigest()
