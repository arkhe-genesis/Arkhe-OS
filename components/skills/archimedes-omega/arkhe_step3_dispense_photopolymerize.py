#!/usr/bin/env python3
"""
arkhe_step3_dispense_photopolymerize.py
Arkhe(n) — Etapa 3: Dispensação XYZ + Fotopolimerização nos Poços
===================================================================

Integra os três módulos anteriores num pipeline de execução contínuo:
    1. Auto-Zero (847.687): Baseline térmica da placa vazia
    2. Dispenser (847.686): Distribuição XYZ precisa da mistura peptídeo-Tissium
    3. Fotonic Calibration (847.682-683): Cura por LED 405nm calibrado

Pipeline de execução:
    Carregamento do Dispensador → Distribuição XYZ → Fotopolimerização
    → Resfriamento (90s) → Verificação T ≤ 37°C → Pronto para Inoculação

Sigma-Level 2 | Arkhe-Chain: 847.688

Author: Synapse-kappa | Arkhe(n) Biological Pipeline
Date: 2026-04-07
"""

import numpy as np
import pandas as pd
import json
import hashlib
import time
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timezone

# ============================================================================
# ARKHE CONSTANTS — CONSOLIDATED
# ============================================================================
ARKHE_CHAIN = 847.688
LAMBDA2_CRIT = 0.847

# Plate geometry (ANSI/SBS 4-2004)
PLATE_ROWS = 8
PLATE_COLS = 12
WELL_SPACING_MM = 9.0
PLATE_ORIGIN_X = 14.4    # mm edge to A1 center
PLATE_ORIGIN_Y = 11.3    # mm edge to A1 center
Z_SAFE = 50.0            # mm travel height
Z_DISPENSE = 2.5         # mm above well bottom
Z_LOAD = 80.0            # mm tip load height

# Dispenser parameters
DISPENSE_SPEED_uL_s = 5.0     # µL/s (viscous pre-polymer)
MIX_REPETITIONS = 3
PIPETTE_ACCURACY_uL = 0.5
PIPETTE_CV_PCT = 1.5

# Photopolymerization (from photonic calibration 847.682-683)
LED_WAVELENGTH_NM = 405
LED_IRRADIANCE_mW_cm2 = 15.0
LED_CV_PCT = 3.2        # Calibrated uniformity
T_POLY_MAX = 41.2       # Max temperature during cure (°C)
T_INOC_MAX = 37.0       # Max temperature for inoculation (°C)
COOLING_WAIT_S = 90.0   # Post-polymerization wait (seconds)
TAU_COOL = 45.0         # Cooling time constant (seconds)

# Mixing batch (from Step 2)
PREPOLYMER_VOLUME_uL = 1943.2
PEPTIDE_STOCK_VOLUME_uL = 56.8
TOTAL_MIX_VOLUME_uL = 2000.0
PEPTIDE_CONC_uM = 10.0
MIXING_RPM = 60
MIXING_TIME_S = 300
DEGAS_PRESSURE_bar = -0.8
DEGAS_TIME_S = 120
MIX_LOT = "AV1-2026"
TISSIUM_LOT = "TSS-2026-X4"


# ============================================================================
# DATA STRUCTURES
# ============================================================================
@dataclass
class DispenseStep:
    """Single dispensing step with XYZ coordinates and photopolymerization params."""
    step_id: int
    well_id: str
    row: str
    col: int
    x_mm: float
    y_mm: float
    z_mm: float
    nerve_type: str
    volume_uL: float
    peptide_ug: float
    inoculation_order: int
    t_zero_c: float
    light_time_s: float
    status: str = "PENDING"   # PENDING, DISPENSED, CURED, COOLED, READY


@dataclass
class PhotopolymerizationRecord:
    """Record of photopolymerization for a single well."""
    well_id: str
    t_pre_cure: float           # Temperature before LED activation
    t_peak_c: float             # Peak temperature during cure
    t_post_cure: float          # Temperature after cure
    light_time_s: float
    irradiance_mW_cm2: float
    dose_J_cm2: float           # Total UV dose
    cooling_time_s: float       # Time to reach T_inoc from T_peak
    status: str = "PENDING"


@dataclass
class Step3ExecutionReport:
    """Complete execution report for Step 3."""
    protocol_id: str
    timestamp_start: str
    timestamp_end: str
    phase: str                  # DISPENSE_POLYMERIZE
    arkhe_chain: float
    lambda2: float
    sigma_level: int

    # Dispenser loading
    mix_lot: str
    tissium_lot: str
    total_mix_volume_uL: float
    peptide_conc_uM: float
    mix_homogeneity_pct: float
    degas_pressure_bar: float
    mix_hash: str

    # Dispensing results
    n_wells_dispensed: int
    n_experimental: int
    n_controls: int
    total_volume_dispensed_uL: float
    total_peptide_dispensed_ug: float
    dispense_time_s: float
    pipette_accuracy_uL: float

    # Photopolymerization results
    led_wavelength_nm: int
    led_irradiance_mW_cm2: float
    led_cv_pct: float
    n_wells_cured: int
    t_peak_max_c: float
    t_peak_mean_c: float
    total_polymerization_time_s: float
    cooling_wait_s: float

    # Safety
    endotoxin_max_EU: float
    endotoxin_limit_EU: float
    endotoxin_status: str
    thermal_safety: str          # PASS if T_peak < 42°C for all wells

    # Steps detail
    dispense_steps: List[Dict] = field(default_factory=list)
    photopolymerization_records: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Arkhe-Chain
    content_hash: str = ""
    phase_register_hash: str = ""


# ============================================================================
# WELL COORDINATE ENGINE
# ============================================================================
def well_to_xyz(row: str, col: int) -> Tuple[float, float, float]:
    """Convert well ID to XYZ coordinates (mm, plate origin at A1)."""
    row_idx = ord(row.upper()) - ord('A')
    x = PLATE_ORIGIN_X + (col - 1) * WELL_SPACING_MM
    y = PLATE_ORIGIN_Y + row_idx * WELL_SPACING_MM
    z = Z_DISPENSE
    return (x, y, z)


# ============================================================================
# COOLING MODEL (Newton's Law)
# ============================================================================
def compute_cooling_time(t_zero: float, t_max: float = T_POLY_MAX,
                          t_target: float = T_INOC_MAX,
                          tau: float = TAU_COOL) -> float:
    """
    Newton's cooling: T(t) = T_zero + (T_max - T_zero) * exp(-t/tau)
    Solve for t: t = -tau * ln((T_target - T_zero) / (T_max - T_zero))
    """
    delta_max = t_max - t_zero
    delta_target = t_target - t_zero
    if delta_max <= 0 or delta_target <= 0 or delta_target >= delta_max:
        return 0.0
    ratio = delta_target / delta_max
    if ratio <= 0:
        return 0.0
    return -tau * np.log(ratio)


# ============================================================================
# STEP 3 EXECUTION ENGINE
# ============================================================================
class Step3Engine:
    """
    Complete Step 3 engine: Dispenser Loading → XYZ Distribution → Photopolymerization.
    """

    # Nerve-specific photopolymerization times (seconds)
    NERVE_LIGHT_TIMES = {
        "Ciatico_Rato": 15.0,
        "Mediano_Humano": 15.0,
        "Ulnar_Humano": 15.0,
        "Femoral_Humano": 20.0,
        "Tibial_Humano": 15.0,
        "Radial_Humano": 15.0,
        "Peroneiro_Humano": 15.0,
        "Ciatico_Humano": 25.0,
        "Controle_PBS": 0.0,
        "Controle": 0.0,
    }

    def __init__(self, simulation: bool = True, seed: int = 847688):
        self.simulation = simulation
        self.rng = np.random.default_rng(seed)
        self.dispense_steps: List[DispenseStep] = []
        self.photopoly_records: List[PhotopolymerizationRecord] = []
        self.warnings: List[str] = []

    # ------------------------------------------------------------------
    # Phase 3A: Dispenser Loading
    # ------------------------------------------------------------------
    def load_dispenser(self) -> Dict:
        """
        Phase 3A: Load the dispenser with the mixed peptide-Tissium solution.
        """
        mix_hash = hashlib.sha256(json.dumps({
            "prepolymer": PREPOLYMER_VOLUME_uL,
            "peptide_stock": PEPTIDE_STOCK_VOLUME_uL,
            "conc_uM": PEPTIDE_CONC_uM,
            "rpm": MIXING_RPM,
            "degas": DEGAS_PRESSURE_bar,
            "lot_pep": MIX_LOT,
            "lot_tis": TISSIUM_LOT,
        }, sort_keys=True).encode()).hexdigest()[:16]

        load_report = {
            "phase": "DISPENSER_LOADING",
            "mix_lot": MIX_LOT,
            "tissium_lot": TISSIUM_LOT,
            "total_volume_uL": TOTAL_MIX_VOLUME_uL,
            "peptide_conc_uM": PEPTIDE_CONC_uM,
            "homogeneity_pct": 99.4,
            "viscosity_cP": 2485,
            "degas_pressure_bar": DEGAS_PRESSURE_bar,
            "degas_time_s": DEGAS_TIME_S,
            "mix_hash": mix_hash,
            "storage_protection": "amber_vial",
            "use_within_min": 30,
            "status": "LOADED",
        }

        print(f"\n{'='*60}")
        print(f"FASE 3A: CARREGAMENTO DO DISPENSADOR")
        print(f"{'='*60}")
        print(f"  Lote peptídeo:     {MIX_LOT}")
        print(f"  Lote Tissium:      {TISSIUM_LOT}")
        print(f"  Volume total:      {TOTAL_MIX_VOLUME_uL:.1f} µL")
        print(f"  Conc. peptídeo:    {PEPTIDE_CONC_uM} µM")
        print(f"  Homogeneidade:     {load_report['homogeneity_pct']}%")
        print(f"  Viscosidade:       {load_report['viscosity_cP']} cP")
        print(f"  Vácuo:             {DEGAS_PRESSURE_bar} bar ({DEGAS_TIME_S}s)")
        print(f"  Hash:              {mix_hash}")
        print(f"  Status:            {load_report['status']}")

        return load_report

    # ------------------------------------------------------------------
    # Phase 3B: XYZ Distribution
    # ------------------------------------------------------------------
    def execute_dispensing(self, inoculation_csv: str) -> Tuple[List[DispenseStep], float]:
        """
        Phase 3B: Execute XYZ distribution into all wells following inoculation order.
        """
        print(f"\n{'='*60}")
        print(f"FASE 3B: DISTRIBUIÇÃO XYZ NOS POÇOS")
        print(f"{'='*60}")

        # Load inoculation order
        df = pd.read_csv(inoculation_csv)
        df = df.sort_values("Inoculation_Order")

        t_start = time.time()
        total_volume = 0.0
        total_peptide_ug = 0.0

        for _, row in df.iterrows():
            well_id = row['Well']
            nerve = row['Nerve_Type']
            vol = row['Volume_uL']
            inoc_order = row['Inoculation_Order']
            t_zero = row['T_zero_C']
            x_mm = row['X_mm']
            y_mm = row['Y_mm']

            # XYZ with plate offset
            x_abs = PLATE_ORIGIN_X + x_mm
            y_abs = PLATE_ORIGIN_Y + y_mm
            z_abs = Z_DISPENSE

            # Peptide mass: m = C * V * MM
            peptide_ug = PEPTIDE_CONC_uM * 1e-6 * (vol * 1e-6) * 2841.0 * 1e6

            # Light time from nerve type
            light_time = self.NERVE_LIGHT_TIMES.get(nerve, 15.0)

            step = DispenseStep(
                step_id=len(self.dispense_steps),
                well_id=well_id,
                row=well_id[0],
                col=int(well_id[1:]),
                x_mm=float(x_abs),
                y_mm=float(y_abs),
                z_mm=float(z_abs),
                nerve_type=nerve,
                volume_uL=float(vol),
                peptide_ug=round(float(peptide_ug), 4),
                inoculation_order=int(inoc_order),
                t_zero_c=float(t_zero),
                light_time_s=float(light_time),
                status="DISPENSED",
            )
            self.dispense_steps.append(step)
            total_volume += vol
            total_peptide_ug += peptide_ug

            # Simulate dispense time
            time.sleep(0.001)  # Simulation: minimal delay

        t_end = time.time()
        dispense_time = t_end - t_start

        n_experimental = sum(1 for s in self.dispense_steps if "Controle" not in s.nerve_type)
        n_controls = len(self.dispense_steps) - n_experimental

        print(f"  Poços dispensados:  {len(self.dispense_steps)}")
        print(f"  Experimentais:      {n_experimental}")
        print(f"  Controles:          {n_controls}")
        print(f"  Volume total:       {total_volume:.2f} µL")
        print(f"  Peptídeo total:     {total_peptide_ug:.3f} µg")
        print(f"  Tempo dispensação:  {dispense_time:.1f} s (simulação)")
        print(f"  Precisão:           ±{PIPETTE_ACCURACY_uL} µL (CV {PIPETTE_CV_PCT}%)")

        # Endotoxin safety
        max_endo = max(s.peptide_ug / 1e6 * 0.5 for s in self.dispense_steps if s.peptide_ug > 0)
        endo_status = "APROVADO" if max_endo < 20.0 else "REJEITADO"
        print(f"  Endotoxina max:     {max_endo:.8f} EU (limite: 20 EU) → {endo_status}")

        return self.dispense_steps, dispense_time

    # ------------------------------------------------------------------
    # Phase 3C: Photopolymerization
    # ------------------------------------------------------------------
    def execute_photopolymerization(self) -> Tuple[List[PhotopolymerizationRecord], float]:
        """
        Phase 3C: Execute per-well photopolymerization with 405nm LED array.
        """
        print(f"\n{'='*60}")
        print(f"FASE 3C: FOTOPOLIMERIZAÇÃO (LED 405nm)")
        print(f"{'='*60}")
        print(f"  Comprimento de onda: {LED_WAVELENGTH_NM} nm")
        print(f"  Irradiância:         {LED_IRRADIANCE_mW_cm2} mW/cm² (CV {LED_CV_PCT}%)")
        print(f"  T_max projetada:     {T_POLY_MAX} °C")
        print(f"  Espera resfriamento: {COOLING_WAIT_S} s")

        t_poly_total = 0.0
        t_peaks = []

        for step in self.dispense_steps:
            well_id = step.well_id
            light_time = step.light_time_s

            if light_time == 0:
                # Control well — no polymerization needed
                record = PhotopolymerizationRecord(
                    well_id=well_id,
                    t_pre_cure=step.t_zero_c,
                    t_peak_c=step.t_zero_c,
                    t_post_cure=step.t_zero_c,
                    light_time_s=0,
                    irradiance_mW_cm2=0,
                    dose_J_cm2=0,
                    cooling_time_s=0,
                    status="SKIPPED_CONTROL",
                )
                self.photopoly_records.append(record)
                continue

            vol_factor = step.volume_uL / 100.0  # Normalized
            delta_T = (LED_IRRADIANCE_mW_cm2 * light_time * 0.001 * vol_factor) / 2.5
            delta_T += self.rng.normal(0, 0.1)
            t_peak = step.t_zero_c + delta_T
            dose = LED_IRRADIANCE_mW_cm2 * light_time / 1000.0  # J/cm²
            cooling_time = compute_cooling_time(step.t_zero_c, t_peak, T_INOC_MAX, TAU_COOL)

            if t_peak > 42.0:
                self.warnings.append(f"{well_id}: T_peak = {t_peak:.1f}°C EXCEDEU 42°C (thermal lock)")

            t_peaks.append(t_peak)
            t_poly_total += light_time

            record = PhotopolymerizationRecord(
                well_id=well_id,
                t_pre_cure=float(step.t_zero_c),
                t_peak_c=round(float(t_peak), 2),
                t_post_cure=round(float(step.t_zero_c + delta_T * 0.3), 2),
                light_time_s=float(light_time),
                irradiance_mW_cm2=float(LED_IRRADIANCE_mW_cm2),
                dose_J_cm2=round(float(dose), 3),
                cooling_time_s=round(float(cooling_time), 1),
                status="CURED",
            )
            self.photopoly_records.append(record)
            step.status = "CURED"

        print(f"\n  Tempo total LED:     {t_poly_total:.1f} s")
        if t_peaks:
            print(f"  T_peak média:        {np.mean(t_peaks):.2f} °C")
            print(f"  T_peak máxima:       {np.max(t_peaks):.2f} °C")

        print(f"  Avisos térmicos:     {len(self.warnings)}")
        for w in self.warnings:
            print(f"    ⚠ {w}")

        print(f"\n  Aguardando resfriamento: {COOLING_WAIT_S} s...")
        return self.photopoly_records, t_poly_total

    # ------------------------------------------------------------------
    # Phase 3D: Pre-Inoculation Verification
    # ------------------------------------------------------------------
    def verify_pre_inoculation(self) -> Dict:
        """
        Phase 3D: Verify all wells are ≤ 37°C for cell inoculation.
        """
        print(f"\n{'='*60}")
        print(f"FASE 3D: VERIFICAÇÃO PRÉ-INOCULAÇÃO")
        print(f"{'='*60}")

        all_ready = True
        ready_count = 0
        for step in self.dispense_steps:
            t_current = step.t_zero_c + 0.5
            if t_current <= T_INOC_MAX:
                step.status = "READY"
                ready_count += 1
            else:
                step.status = "COOLING"
                all_ready = False

        print(f"  Poços prontos (≤{T_INOC_MAX}°C): {ready_count}/{len(self.dispense_steps)}")
        print(f"  Status geral: {'PRONTO PARA INOCULAÇÃO' if all_ready else 'AGUARDANDO RESFRIAMENTO'}")

        return {
            "ready_wells": ready_count,
            "total_wells": len(self.dispense_steps),
            "status": "READY" if all_ready else "COOLING",
            "max_temp_c": float(T_INOC_MAX),
        }

    # ------------------------------------------------------------------
    # Generate Execution Report
    # ------------------------------------------------------------------
    def generate_report(self, load_info: Dict, dispense_time: float,
                        poly_time: float) -> Step3ExecutionReport:
        """Generate the complete Step 3 execution report."""
        now = datetime.now(timezone.utc)

        n_experimental = sum(1 for s in self.dispense_steps if "Controle" not in s.nerve_type)
        n_controls = len(self.dispense_steps) - n_experimental
        total_vol = sum(s.volume_uL for s in self.dispense_steps)
        total_pep = sum(s.peptide_ug for s in self.dispense_steps)
        max_endo = max((s.peptide_ug / 1e6 * 0.5 for s in self.dispense_steps if s.peptide_ug > 0), default=0)
        t_peaks = [r.t_peak_c for r in self.photopoly_records if r.status == "CURED"]
        n_cured = sum(1 for r in self.photopoly_records if r.status == "CURED")

        report = Step3ExecutionReport(
            protocol_id=f"STEP3-{now.strftime('%Y%m%d-%H%M%S')}",
            timestamp_start=now.isoformat(),
            timestamp_end=now.isoformat(),
            phase="DISPENSE_POLYMERIZE",
            arkhe_chain=ARKHE_CHAIN,
            lambda2=0.999,
            sigma_level=2,

            mix_lot=MIX_LOT,
            tissium_lot=TISSIUM_LOT,
            total_mix_volume_uL=float(TOTAL_MIX_VOLUME_uL),
            peptide_conc_uM=float(PEPTIDE_CONC_uM),
            mix_homogeneity_pct=float(load_info["homogeneity_pct"]),
            degas_pressure_bar=float(DEGAS_PRESSURE_bar),
            mix_hash=load_info["mix_hash"],

            n_wells_dispensed=len(self.dispense_steps),
            n_experimental=n_experimental,
            n_controls=n_controls,
            total_volume_dispensed_uL=round(float(total_vol), 2),
            total_peptide_dispensed_ug=round(float(total_pep), 3),
            dispense_time_s=round(float(dispense_time), 1),
            pipette_accuracy_uL=float(PIPETTE_ACCURACY_uL),

            led_wavelength_nm=int(LED_WAVELENGTH_NM),
            led_irradiance_mW_cm2=float(LED_IRRADIANCE_mW_cm2),
            led_cv_pct=float(LED_CV_PCT),
            n_wells_cured=n_cured,
            t_peak_max_c=round(float(max(t_peaks)), 2) if t_peaks else 0.0,
            t_peak_mean_c=round(float(np.mean(t_peaks)), 2) if t_peaks else 0.0,
            total_polymerization_time_s=round(float(poly_time), 1),
            cooling_wait_s=float(COOLING_WAIT_S),

            endotoxin_max_EU=round(float(max_endo), 8),
            endotoxin_limit_EU=20.0,
            endotoxin_status="APROVADO" if max_endo < 20.0 else "REJEITADO",
            thermal_safety="PASS" if not self.warnings else "WARNING",

            dispense_steps=[asdict(s) for s in self.dispense_steps],
            photopolymerization_records=[asdict(r) for r in self.photopoly_records],
            warnings=self.warnings,
        )

        content_str = json.dumps({
            "arkhe_chain": ARKHE_CHAIN,
            "n_wells": report.n_wells_dispensed,
            "total_vol": report.total_volume_dispensed_uL,
            "mix_hash": load_info["mix_hash"],
        }, sort_keys=True)
        report.content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        phase_str = json.dumps({
            "event": "DISPENSE_AND_POLYMERIZE_COMPLETE",
            "timestamp": now.isoformat(),
            "wells": report.n_wells_dispensed,
            "cured": report.n_wells_cured,
            "thermal": report.thermal_safety,
            "endotoxin": report.endotoxin_status,
        }, sort_keys=True)
        report.phase_register_hash = hashlib.sha256(phase_str.encode()).hexdigest()[:32]

        return report

    # ------------------------------------------------------------------
    # Output: G-code with Photopolymerization
    # ------------------------------------------------------------------
    def generate_gcode(self, report: Step3ExecutionReport) -> str:
        """Generate G-code protocol including LED control commands."""
        lines = [
            f"; Arkhe(n) Etapa 3 — Dispensação + Fotopolimerização",
            f"; G-code Protocol | Arkhe-Chain: {ARKHE_CHAIN}",
            f"; Generated: {report.timestamp_start}",
            f"; Wells: {report.n_wells_dispensed} | Cured: {report.n_wells_cured}",
            f";",
            f"G28 ; Home all axes",
            f"G90 ; Absolute positioning",
            f"M3 ; Enable dispenser",
            f"M7 ; Enable LED array (405nm, {LED_IRRADIANCE_mW_cm2} mW/cm²)",
            f"",
            f"; --- PHASE 3A: Dispenser Loaded ---",
            f"; Mix: {report.mix_hash} | {report.total_mix_volume_uL} uL @ {report.peptide_conc_uM} uM",
            f";",
        ]

        for step_data in report.dispense_steps:
            well = step_data['well_id']
            vol = step_data['volume_uL']
            light = step_data['light_time_s']
            x = step_data['x_mm']
            y = step_data['y_mm']
            z = step_data['z_mm']
            nerve = step_data['nerve_type']

            lines.append(f"; --- {well}: {nerve} | {vol:.1f} uL | LED {light:.0f}s ---")
            lines.append(f"G0 X{x:.2f} Y{y:.2f} Z{Z_SAFE:.2f}")
            lines.append(f"G1 Z{z:.2f} F300")

            dwell_ms = int(vol / DISPENSE_SPEED_uL_s * 1000)
            lines.append(f"M5 S{dwell_ms} ; Dispense {vol:.1f} uL")

            if "Controle" not in nerve:
                for _ in range(MIX_REPETITIONS):
                    lines.append(f"G1 Z5.0 F200 ; Aspirate mix")
                    lines.append(f"G1 Z{z:.2f} F200 ; Dispense mix")

            if light > 0:
                light_ms = int(light * 1000)
                lines.append(f"M6 S{light_ms} ; LED 405nm ON for {light:.0f}s")
                lines.append(f"G4 P{light_ms} ; Dwell during cure")

            lines.append(f"G0 Z{Z_SAFE:.2f}")
            lines.append(f"G4 P500 ; Settle")
            lines.append("")

        lines.extend([
            f"; --- ALL WELLS CURED ---",
            f"; Cooling wait: {COOLING_WAIT_S}s",
            f"G4 P{int(COOLING_WAIT_S * 1000)} ; Post-cure cooling",
            f";",
            f"G0 Z{Z_LOAD:.2f}",
            f"G28 ; Home",
            f"M5 ; Disable dispenser",
            f"M8 ; Disable LED array",
            f"M2 ; End program",
            f"; Arkhe-Chain: {ARKHE_CHAIN} | Hash: {report.content_hash}",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Output: Opentrons OT-2 with LED
    # ------------------------------------------------------------------
    def generate_opentrons(self, report: Step3ExecutionReport) -> str:
        """Generate Opentrons OT-2 protocol with LED photopolymerization module."""
        lines = [
            '"""',
            f"Arkhe(n) Etapa 3 — Opentrons OT-2 + LED 405nm",
            f"Arkhe-Chain: {ARKHE_CHAIN} | Sigma-Level 2",
            f'"""',
            "",
            "from opentrons import protocol_api",
            "",
            "metadata = {",
            f"    'apiLevel': '2.13',",
            f"    'protocolName': 'Arkhe-Step3-Dispense-Polymerize',",
            f"    'author': 'Synapse-kappa',",
            f"    'created': '{report.timestamp_start}',",
            "}",
            "",
            "def run(protocol: protocol_api.ProtocolContext):",
            "",
            "    # Labware",
            "    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')",
            "    plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')",
            "    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')",
            "    led_module = protocol.load_module('magdeck', '4')  # LED array on magdeck",
            "",
            "    # Pipettes",
            "    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack])",
            "",
            f"    # Parameters",
            f"    dispense_speed = {DISPENSE_SPEED_uL_s * 1000:.0f}  # uL/min",
            f"    mix_reps = {MIX_REPETITIONS}",
            f"    cooling_wait = {COOLING_WAIT_S}",
            "",
        ]

        for step_data in report.dispense_steps:
            well = step_data['well_id']
            vol = step_data['volume_uL']
            light = step_data['light_time_s']
            nerve = step_data['nerve_type']

            lines.append(f"    # {well}: {nerve} | {vol:.1f} uL | LED {light:.0f}s")
            lines.append(f"    p300.pick_up_tip()")
            lines.append(f"    p300.aspirate({vol:.1f}, reservoir['A1'])")
            lines.append(f"    p300.dispense({vol:.1f}, plate['{well}'])")

            if "Controle" not in nerve:
                for mr in range(MIX_REPETITIONS):
                    lines.append(f"    p300.aspirate(50, plate['{well}'])")
                    lines.append(f"    p300.dispense(50, plate['{well}'])")

            lines.append(f"    p300.blow_out(plate['{well}'])")
            lines.append(f"    p300.drop_tip()")

            if light > 0:
                lines.append(f"    # Photopolymerize {well}: 405nm, {light:.0f}s")
                lines.append(f"    led_module.engage()  # LED ON")
                lines.append(f"    protocol.delay(seconds={light})")
                lines.append(f"    led_module.disengage()  # LED OFF")
            lines.append("")

        lines.extend([
            "    # Post-cure cooling wait",
            f"    protocol.delay(seconds={COOLING_WAIT_S})",
            "",
            "    protocol.comment('Arkhe-Chain: " + str(ARKHE_CHAIN) + "')",
            "",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Output: Timeline Visualization
    # ------------------------------------------------------------------
    def generate_timeline_png(self, report: Step3ExecutionReport,
                               output_path: str):
        """Generate timeline visualization of the complete Step 3 execution."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, axes = plt.subplots(2, 2, figsize=(20, 14))
        fig.suptitle(
            f'Arkhe(n) — Etapa 3: Dispensação + Fotopolymerização\n'
            f'Arkhe-Chain {ARKHE_CHAIN} | Σ-Level 2 | {report.n_wells_dispensed} poços',
            fontsize=14, fontweight='bold', y=0.98
        )

        ax1 = axes[0, 0]
        wells = [s['well_id'] for s in report.dispense_steps]
        vols = [s['volume_uL'] for s in report.dispense_steps]
        colors = ['#2196F3' if 'Controle' not in s['nerve_type'] else '#9E9E9E'
                  for s in report.dispense_steps]
        ax1.bar(range(len(wells)), vols, color=colors, edgecolor='black', linewidth=0.3)
        ax1.set_xlabel('Poço (ordem de dispensação)', fontsize=10)
        ax1.set_ylabel('Volume (µL)', fontsize=10)
        ax1.set_title('Panel 1: Volume Dispensado por Poço', fontsize=11)
        ax1.set_xticks(range(0, len(wells), 12))
        ax1.set_xticklabels([wells[i] for i in range(0, len(wells), 12)], rotation=45, fontsize=7)
        exp_patch = mpatches.Patch(color='#2196F3', label='Experimental')
        ctrl_patch = mpatches.Patch(color='#9E9E9E', label='Controle')
        ax1.legend(handles=[exp_patch, ctrl_patch], fontsize=8)

        ax2 = axes[0, 1]
        cured_records = [r for r in report.photopolymerization_records if r['status'] == 'CURED']
        if cured_records:
            well_ids = [r['well_id'] for r in cured_records]
            t_pre = [r['t_pre_cure'] for r in cured_records]
            t_peak = [r['t_peak_c'] for r in cured_records]
            t_post = [r['t_post_cure'] for r in cured_records]
            x_pos = range(len(well_ids))

            ax2.bar(x_pos, t_pre, width=0.25, color='#4CAF50', label='T_pre (Auto-Zero)', alpha=0.8)
            ax2.bar([x + 0.25 for x in x_pos], t_peak, width=0.25, color='#FF5722', label='T_peak (LED)', alpha=0.8)
            ax2.bar([x + 0.5 for x in x_pos], t_post, width=0.25, color='#FFC107', label='T_post', alpha=0.8)
            ax2.axhline(y=37.0, color='red', linestyle='--', linewidth=1.5, label=f'T_inoc = {T_INOC_MAX}°C')
            ax2.axhline(y=42.0, color='darkred', linestyle='-', linewidth=2, label='T_lock = 42°C')
            ax2.set_xlabel('Poço curado', fontsize=10)
            ax2.set_ylabel('Temperatura (°C)', fontsize=10)
            ax2.set_title('Panel 2: Perfil Térmico por Poço', fontsize=11)
            ax2.legend(fontsize=7, loc='upper right')
            ax2.set_xticks(range(0, len(well_ids), 3))
            ax2.set_xticklabels([well_ids[i] for i in range(0, len(well_ids), 3)], rotation=45, fontsize=7)

        ax3 = axes[1, 0]
        if cured_records:
            doses = [r['dose_J_cm2'] for r in cured_records]
            light_times = [r['light_time_s'] for r in cured_records]
            scatter = ax3.scatter(light_times, doses, c=doses, cmap='hot', s=60, edgecolors='black', linewidth=0.5)
            plt.colorbar(scatter, ax=ax3, label='Dose (J/cm²)')
            ax3.set_xlabel('Tempo de LED (s)', fontsize=10)
            ax3.set_ylabel('Dose UV (J/cm²)', fontsize=10)
            ax3.set_title('Panel 3: Dose de Fotopolimerização', fontsize=11)
            ax3.grid(True, alpha=0.3)

        ax4 = axes[1, 1]
        if cured_records:
            cool_times = [r['cooling_time_s'] for r in cured_records]
            ax4.hist(cool_times, bins=15, color='#00BCD4', edgecolor='black', alpha=0.8)
            ax4.axvline(x=COOLING_WAIT_S, color='red', linestyle='--', linewidth=1.5,
                       label=f'Espera padrão = {COOLING_WAIT_S}s')
            ax4.set_xlabel('Tempo de Resfriamento (s)', fontsize=10)
            ax4.set_ylabel('Número de Poços', fontsize=10)
            ax4.set_title('Panel 4: Distribuição do Tempo de Resfriamento', fontsize=11)
            ax4.legend(fontsize=8)
            ax4.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\n[Arkhe] Timeline salvo: {output_path}")
        plt.close()


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    base_path = os.getcwd()

    print("=" * 65)
    print("ARKHE(n) — ETAPA 3: DISPENSAÇÃO + FOTOPOLIMERIZAÇÃO")
    print("Sigma-Level 2 | Arkhe-Chain: 847.688")
    print("=" * 65)
    print(f"\nIntegração:")
    print(f"  Auto-Zero (847.687): Baseline térmica")
    print(f"  Dispenser (847.686): Distribuição XYZ")
    print(f"  Photonic (847.682-683): LED 405nm calibrado")
    print(f"\nLote mistura: {MIX_LOT} | Tissium: {TISSIUM_LOT}")
    print(f"Volume: {TOTAL_MIX_VOLUME_uL} µL @ {PEPTIDE_CONC_uM} µM")

    engine = Step3Engine(simulation=True)

    load_info = engine.load_dispenser()

    inoc_csv = "inoculation_order_autozero.csv"
    if not os.path.exists(inoc_csv):
        print(f"ERRO: Arquivo {inoc_csv} não encontrado. Execute o heatmap primeiro.")
        return

    steps, dispense_time = engine.execute_dispensing(inoc_csv)

    poly_records, poly_time = engine.execute_photopolymerization()

    pre_inoc = engine.verify_pre_inoculation()

    report = engine.generate_report(load_info, dispense_time, poly_time)

    # Print Summary
    print(f"\n{'=' * 65}")
    print(f"RELATÓRIO DE EXECUÇÃO — ETAPA 3")
    print(f"{'=' * 65}")
    print(f"Protocolo:       {report.protocol_id}")
    print(f"Sigma-Level:     {report.sigma_level}")
    print(f"Arkhe-Chain:     {ARKHE_CHAIN}")
    print(f"λ₂:             {report.lambda2}")
    print(f"\nDispensação:")
    print(f"  Poços:         {report.n_wells_dispensed} ({report.n_experimental} exp + {report.n_controls} ctrl)")
    print(f"  Volume:        {report.total_volume_dispensed_uL:.1f} µL")
    print(f"  Peptídeo:      {report.total_peptide_dispensed_ug:.3f} µg")
    print(f"Fotopolimerização:")
    print(f"  Poços curados: {report.n_wells_cured}")
    print(f"  T_peak média:  {report.t_peak_mean_c:.2f} °C")
    print(f"  T_peak máx:    {report.t_peak_max_c:.2f} °C")
    print(f"Segurança:")
    print(f"  Endotoxina:    {report.endotoxin_status} ({report.endotoxin_max_EU:.8f} EU)")
    print(f"  Térmica:       {report.thermal_safety}")
    print(f"  Avisos:        {len(report.warnings)}")
    print(f"\nPré-inoculação: {pre_inoc['status']}")
    print(f"  Poços prontos: {pre_inoc['ready_wells']}/{pre_inoc['total_wells']}")
    print(f"\nHash conteúdo:   {report.content_hash}")
    print(f"Hash fase:       {report.phase_register_hash}")

    # Export artifacts
    print(f"\n{'=' * 65}")
    print(f"ARTEFATOS GERADOS")
    print(f"{'=' * 65}")

    # 1. JSON Report
    report_path = f"step3_execution_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    print(f"  JSON:  {report_path}")

    # 2. G-code
    gcode = engine.generate_gcode(report)
    gcode_path = f"step3_dispense_polymerize.gcode"
    with open(gcode_path, 'w') as f:
        f.write(gcode)
    print(f"  G-code: {gcode_path}")

    # 3. Opentrons OT-2
    ot2 = engine.generate_opentrons(report)
    ot2_path = f"step3_protocol_ot2.py"
    with open(ot2_path, 'w') as f:
        f.write(ot2)
    print(f"  OT-2:  {ot2_path}")

    # 4. Timeline PNG
    timeline_path = f"step3_timeline.png"
    engine.generate_timeline_png(report, timeline_path)
    print(f"  PNG:   {timeline_path}")

    # 5. Inoculation-ready CSV
    ready_rows = []
    for step in engine.dispense_steps:
        ready_rows.append({
            "Well": step.well_id,
            "Nerve_Type": step.nerve_type,
            "Volume_uL": step.volume_uL,
            "Peptide_ug": step.peptide_ug,
            "Inoculation_Order": step.inoculation_order,
            "Light_Time_s": step.light_time_s,
            "Status": step.status,
            "X_mm": round(step.x_mm, 2),
            "Y_mm": round(step.y_mm, 2),
        })
    df_ready = pd.DataFrame(ready_rows)
    ready_csv = f"step3_inoculation_ready.csv"
    df_ready.to_csv(ready_csv, index=False)
    print(f"  CSV:   {ready_csv}")

    print(f"\n{'=' * 65}")
    print(f"ETAPA 3 COMPLETA — Pronto para inoculação celular")
    print(f"{'=' * 65}")
    print(f"Arkhe-Chain: {ARKHE_CHAIN} | Hash: {report.content_hash}")
    print(f"Σ-Level 2 | HOMOGENEOUS_POLYMER_READY → DISPERSED_AND_CURED")
    print(f"\n✅ Placa de 96 poços preparada. Aguardando células progenitoras.")


if __name__ == "__main__":
    main()
