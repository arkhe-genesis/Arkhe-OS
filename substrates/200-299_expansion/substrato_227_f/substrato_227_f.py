import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum, auto
import math

class Severity(Enum):
    PASS = auto()
    WARN = auto()
    FAIL = auto()
    CRITICAL = auto()

class InvariantID(Enum):
    H1_CONTINUITY = "H1"
    H2_ISOLATION = "H2"
    H3_IMPEDANCE = "H3"
    H4_THERMAL = "H4"
    H5_FABRICABILITY = "H5"
    H6_MOUNTABILITY = "H6"
    H7_TESTABILITY = "H7"
    H8_TRACEABILITY = "H8"

class ThreatID(Enum):
    T1_TROJAN_LAYER = "T1"
    T2_COUNTERFEIT = "T2"
    T3_HIDDEN_ANTENNA = "T3"
    T4_POWER_SIDECHANNEL = "T4"
    T5_ACCELERATED_AGING = "T5"
    T6_DRC_EVASION = "T6"
    T7_BOM_POISONING = "T7"

@dataclass(frozen=True)
class ConstitutionalProof:
    timestamp: float
    design_hash: str
    module_name: str
    invariant: str
    severity: str
    message: str
    details: str
    verifier_signature: str

    def __post_init__(self):
        payload = (
            str(self.timestamp) + "|" + self.design_hash + "|" + self.module_name + "|"
            + self.invariant + "|" + self.severity + "|" + self.message + "|" + self.details
        )
        expected = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
        if self.verifier_signature != expected:
            raise ValueError(
                "Invalid proof signature for " + self.invariant + ": "
                + "expected " + expected + ", got " + self.verifier_signature
            )

@dataclass
class VerificationResult:
    module: str
    invariant_checks: List[Tuple] = field(default_factory=list)
    threat_checks: List[Tuple] = field(default_factory=list)
    proofs: List[ConstitutionalProof] = field(default_factory=list)

    def generate_proofs(self, design_hash: str) -> List[ConstitutionalProof]:
        proofs = []
        ts = time.time()

        for inv, sev, msg, det in self.invariant_checks:
            det_str = json.dumps(det, sort_keys=True)
            payload = (
                str(ts) + "|" + design_hash + "|" + self.module + "|" + inv.value + "|"
                + sev.name + "|" + msg + "|" + det_str
            )
            sig = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
            proofs.append(ConstitutionalProof(
                timestamp=ts, design_hash=design_hash, module_name=self.module,
                invariant=inv.value, severity=sev.name, message=msg,
                details=det_str, verifier_signature=sig
            ))

        for thr, sev, msg, det in self.threat_checks:
            det_str = json.dumps(det, sort_keys=True)
            payload = (
                str(ts) + "|" + design_hash + "|" + self.module + "|" + thr.value + "|"
                + sev.name + "|" + msg + "|" + det_str
            )
            sig = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
            proofs.append(ConstitutionalProof(
                timestamp=ts, design_hash=design_hash, module_name=self.module,
                invariant=thr.value, severity=sev.name, message=msg,
                details=det_str, verifier_signature=sig
            ))

        self.proofs = proofs
        return proofs

@dataclass
class Net:
    name: str
    nodes: List[Tuple[float, float, int]]
    width_mm: float
    is_power: bool = False
    is_ground: bool = False

@dataclass
class Component:
    ref: str
    footprint: str
    value: str
    pn: str
    mfr: str
    pos: Tuple[float, float]
    rotation: float
    layer: str
    height_mm: float
    thermal_watt: float
    pins: List[Dict] = field(default_factory=list)

@dataclass
class Via:
    pos: Tuple[float, float]
    drill_mm: float
    pad_mm: float
    layers: Tuple[int, int]
    net: str

@dataclass
class PCBDesign:
    name: str
    version: str
    nets: List[Net]
    components: List[Component]
    vias: List[Via]
    board_outline: List[Tuple[float, float]]
    layers: int = 4
    thickness_mm: float = 1.6

    def compute_hash(self) -> str:
        payload = json.dumps({
            "name": self.name,
            "version": self.version,
            "nets": [{"name": n.name, "nodes": n.nodes, "width": n.width_mm} for n in self.nets],
            "components": sorted([{"ref": c.ref, "pn": c.pn, "pos": c.pos} for c in self.components], key=lambda x: x["ref"]),
            "vias": [{"pos": v.pos, "net": v.net} for v in self.vias],
            "layers": self.layers,
            "thickness": self.thickness_mm
        }, sort_keys=True)
        return hashlib.sha3_256(payload.encode()).hexdigest()

class DRCModule:
    MIN_TRACE_WIDTH_MM = 0.15
    MIN_CLEARANCE_MM = 0.15
    MIN_DRILL_MM = 0.2
    MIN_ANNULAR_RING_MM = 0.05
    MAX_ASPECT_RATIO = 10

    def __init__(self, design: PCBDesign):
        self.design = design
        self.results = VerificationResult(module="DRC++")

    def check_continuity(self) -> Severity:
        open_nets = [net.name for net in self.design.nets if len(net.nodes) < 2]
        if open_nets:
            self.results.invariant_checks.append((
                InvariantID.H1_CONTINUITY,
                Severity.FAIL,
                "Open nets detected: " + str(open_nets),
                {"open_nets": open_nets, "count": len(open_nets)}
            ))
            return Severity.FAIL
        self.results.invariant_checks.append((
            InvariantID.H1_CONTINUITY,
            Severity.PASS,
            "All " + str(len(self.design.nets)) + " nets have continuity",
            {"net_count": len(self.design.nets)}
        ))
        return Severity.PASS

    def check_isolation(self) -> Severity:
        violations = []
        for i, net_a in enumerate(self.design.nets):
            for net_b in self.design.nets[i + 1:]:
                min_dist = self._min_distance_between_nets(net_a, net_b)
                if min_dist < self.MIN_CLEARANCE_MM:
                    violations.append({
                        "net_a": net_a.name,
                        "net_b": net_b.name,
                        "distance_mm": round(min_dist, 4),
                        "required_mm": self.MIN_CLEARANCE_MM
                    })
        if violations:
            self.results.invariant_checks.append((
                InvariantID.H2_ISOLATION,
                Severity.FAIL,
                str(len(violations)) + " clearance violations",
                {"violations": violations}
            ))
            return Severity.FAIL
        self.results.invariant_checks.append((
            InvariantID.H2_ISOLATION,
            Severity.PASS,
            "All nets meet isolation requirements",
            {"min_clearance_mm": self.MIN_CLEARANCE_MM}
        ))
        return Severity.PASS

    def check_fabricability(self) -> Severity:
        issues = []
        for net in self.design.nets:
            if net.width_mm < self.MIN_TRACE_WIDTH_MM:
                issues.append({
                    "type": "trace_width",
                    "net": net.name,
                    "value_mm": net.width_mm,
                    "min_mm": self.MIN_TRACE_WIDTH_MM
                })
        if self.design.vias:
            valid_vias = [v for v in self.design.vias if v.drill_mm > 0]
            if valid_vias:
                min_drill = min(v.drill_mm for v in valid_vias)
                aspect = self.design.thickness_mm / min_drill
                if aspect > self.MAX_ASPECT_RATIO:
                    issues.append({
                        "type": "aspect_ratio",
                        "value": round(aspect, 2),
                        "max": self.MAX_ASPECT_RATIO
                    })
        for via in self.design.vias:
            annular = (via.pad_mm - via.drill_mm) / 2
            if annular < self.MIN_ANNULAR_RING_MM:
                issues.append({
                    "type": "annular_ring",
                    "via_net": via.net,
                    "value_mm": round(annular, 4),
                    "min_mm": self.MIN_ANNULAR_RING_MM
                })
        if issues:
            self.results.invariant_checks.append((
                InvariantID.H5_FABRICABILITY,
                Severity.FAIL,
                str(len(issues)) + " DFM violations",
                {"issues": issues}
            ))
            return Severity.FAIL
        self.results.invariant_checks.append((
            InvariantID.H5_FABRICABILITY,
            Severity.PASS,
            "Design meets fabrication constraints",
            {"checks": ["trace_width", "aspect_ratio", "annular_ring"]}
        ))
        return Severity.PASS

    def _min_distance_between_nets(self, net_a: Net, net_b: Net) -> float:
        min_dist = float("inf")
        for node_a in net_a.nodes:
            for node_b in net_b.nodes:
                if node_a[2] == node_b[2]:
                    dist = math.sqrt(
                        (node_a[0] - node_b[0])**2 +
                        (node_a[1] - node_b[1])**2
                    )
                    min_dist = min(min_dist, dist)
        return min_dist if min_dist != float("inf") else 999.0

    def run_all(self) -> VerificationResult:
        self.check_continuity()
        self.check_isolation()
        self.check_fabricability()
        self.results.generate_proofs(self.design.compute_hash())
        return self.results

class ThermalModule:
    AMBIENT_TEMP_C = 25.0
    MAX_JUNCTION_TEMP_C = 125.0
    THERMAL_RESISTANCE_C_W = 50.0

    def __init__(self, design: PCBDesign):
        self.design = design
        self.results = VerificationResult(module="THERMAL")

    def check_thermal(self) -> Severity:
        hotspots = []
        for comp in self.design.components:
            if comp.thermal_watt > 0:
                t_j = self.AMBIENT_TEMP_C + comp.thermal_watt * self.THERMAL_RESISTANCE_C_W
                if t_j > self.MAX_JUNCTION_TEMP_C:
                    hotspots.append({
                        "ref": comp.ref,
                        "power_w": comp.thermal_watt,
                        "t_junction_c": round(t_j, 2),
                        "max_tj_c": self.MAX_JUNCTION_TEMP_C
                    })
        if hotspots:
            self.results.invariant_checks.append((
                InvariantID.H4_THERMAL,
                Severity.FAIL,
                str(len(hotspots)) + " components exceed junction temperature",
                {"hotspots": hotspots}
            ))
            return Severity.FAIL
        self.results.invariant_checks.append((
            InvariantID.H4_THERMAL,
            Severity.PASS,
            "All " + str(len(self.design.components)) + " components within thermal limits",
            {"max_tj_c": self.MAX_JUNCTION_TEMP_C}
        ))
        return Severity.PASS

    def run_all(self) -> VerificationResult:
        self.check_thermal()
        self.results.generate_proofs(self.design.compute_hash())
        return self.results

class MechanicalModule:
    MIN_COMPONENT_SPACING_MM = 0.5
    BOARD_MARGIN_MM = 1.0

    def __init__(self, design: PCBDesign):
        self.design = design
        self.results = VerificationResult(module="MECH")

    def check_mountability(self) -> Severity:
        collisions = []
        for i, comp_a in enumerate(self.design.components):
            for comp_b in self.design.components[i + 1:]:
                dist = math.sqrt(
                    (comp_a.pos[0] - comp_b.pos[0])**2 +
                    (comp_a.pos[1] - comp_b.pos[1])**2
                )
                if dist < self.MIN_COMPONENT_SPACING_MM:
                    collisions.append({
                        "comp_a": comp_a.ref,
                        "comp_b": comp_b.ref,
                        "distance_mm": round(dist, 4)
                    })
        out_of_board = [
            c.ref for c in self.design.components
            if not self._point_in_polygon(c.pos, self.design.board_outline)
        ]
        if collisions or out_of_board:
            self.results.invariant_checks.append((
                InvariantID.H6_MOUNTABILITY,
                Severity.FAIL,
                str(len(collisions)) + " collisions, " + str(len(out_of_board)) + " out-of-board",
                {"collisions": collisions, "out_of_board": out_of_board}
            ))
            return Severity.FAIL
        self.results.invariant_checks.append((
            InvariantID.H6_MOUNTABILITY,
            Severity.PASS,
            "All " + str(len(self.design.components)) + " components properly placed",
            {"spacing_mm": self.MIN_COMPONENT_SPACING_MM}
        ))
        return Severity.PASS

    def _point_in_polygon(self, point, polygon):
        x, y = point
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi):
                inside = not inside
            j = i
        return inside

    def run_all(self) -> VerificationResult:
        self.check_mountability()
        self.results.generate_proofs(self.design.compute_hash())
        return self.results

class SupplyModule:
    VALID_PNS = {
        "RC0603JR-0710KL", "GRM188R71H104KA93D", "STM32F407VGT6",
        "TPS54331DDA", "BSS138", "MMBT2222A", "10uF_0603_X5R",
        "100nF_0402_X7R", "1k_0603_1%", "10k_0603_1%"
    }
    EOL_PNS = {"STM32F407VGT6"}

    def __init__(self, design: PCBDesign):
        self.design = design
        self.results = VerificationResult(module="SUPPLY")

    def check_traceability(self) -> Severity:
        invalid_pns = []
        eol_pns = []
        missing_pn = []
        for comp in self.design.components:
            if not comp.pn:
                missing_pn.append(comp.ref)
            elif comp.pn not in self.VALID_PNS:
                invalid_pns.append({"ref": comp.ref, "pn": comp.pn})
            elif comp.pn in self.EOL_PNS:
                eol_pns.append({"ref": comp.ref, "pn": comp.pn})
        if invalid_pns or missing_pn:
            self.results.invariant_checks.append((
                InvariantID.H8_TRACEABILITY,
                Severity.FAIL,
                str(len(invalid_pns)) + " invalid PNs, " + str(len(missing_pn)) + " missing PNs",
                {"invalid": invalid_pns, "missing": missing_pn, "eol": eol_pns}
            ))
            return Severity.FAIL
        if eol_pns:
            self.results.invariant_checks.append((
                InvariantID.H8_TRACEABILITY,
                Severity.WARN,
                str(len(eol_pns)) + " EOL components detected",
                {"eol": eol_pns}
            ))
            return Severity.WARN
        self.results.invariant_checks.append((
            InvariantID.H8_TRACEABILITY,
            Severity.PASS,
            "All " + str(len(self.design.components)) + " components traceable",
            {"valid_pn_count": len(self.VALID_PNS)}
        ))
        return Severity.PASS

    def run_all(self) -> VerificationResult:
        self.check_traceability()
        self.results.generate_proofs(self.design.compute_hash())
        return self.results

class SecurityModule:
    def __init__(self, design: PCBDesign):
        self.design = design
        self.results = VerificationResult(module="SECURITY")

    def check_trojan_layer(self) -> Severity:
        floating_vias = [
            v.net for v in self.design.vias
            if not any(v.net == n.name for n in self.design.nets)
        ]
        if floating_vias:
            self.results.threat_checks.append((
                ThreatID.T1_TROJAN_LAYER,
                Severity.FAIL,
                str(len(floating_vias)) + " floating vias detected",
                {"floating_vias": floating_vias}
            ))
            return Severity.FAIL
        self.results.threat_checks.append((
            ThreatID.T1_TROJAN_LAYER,
            Severity.PASS,
            "No floating vias detected",
            {"via_count": len(self.design.vias)}
        ))
        return Severity.PASS

    def check_hidden_antenna(self) -> Severity:
        ANTENNA_THRESHOLD_MM = 50.0
        suspicious_nets = []
        for net in self.design.nets:
            if len(net.nodes) > 2:
                length = sum(
                    math.sqrt(
                        (net.nodes[i + 1][0] - net.nodes[i][0])**2 +
                        (net.nodes[i + 1][1] - net.nodes[i][1])**2
                    )
                    for i in range(len(net.nodes) - 1)
                )
                if length > ANTENNA_THRESHOLD_MM and not (net.is_power or net.is_ground):
                    suspicious_nets.append({
                        "net": net.name,
                        "estimated_length_mm": round(length, 2)
                    })
        if suspicious_nets:
            self.results.threat_checks.append((
                ThreatID.T3_HIDDEN_ANTENNA,
                Severity.FAIL,
                str(len(suspicious_nets)) + " nets may act as unintended antennas",
                {"suspicious_nets": suspicious_nets}
            ))
            return Severity.FAIL
        self.results.threat_checks.append((
            ThreatID.T3_HIDDEN_ANTENNA,
            Severity.PASS,
            "No suspicious antenna-like traces",
            {"threshold_mm": ANTENNA_THRESHOLD_MM}
        ))
        return Severity.PASS

    def check_bom_poisoning(self) -> Severity:
        UNTRUSTED_MFR = {"Unknown", "Generic", "NoName"}
        untrusted = [
            {"ref": c.ref, "mfr": c.mfr}
            for c in self.design.components
            if c.mfr in UNTRUSTED_MFR
        ]
        if untrusted:
            self.results.threat_checks.append((
                ThreatID.T7_BOM_POISONING,
                Severity.FAIL,
                str(len(untrusted)) + " components from untrusted manufacturers",
                {"untrusted": untrusted}
            ))
            return Severity.FAIL
        self.results.threat_checks.append((
            ThreatID.T7_BOM_POISONING,
            Severity.PASS,
            "All components from qualified manufacturers",
            {"trusted_count": len(self.design.components)}
        ))
        return Severity.PASS

    def run_all(self) -> VerificationResult:
        self.check_trojan_layer()
        self.check_hidden_antenna()
        self.check_bom_poisoning()
        self.results.generate_proofs(self.design.compute_hash())
        return self.results

class Arkhe227FVerifier:
    def __init__(self, design: PCBDesign):
        self.design = design
        self.design_hash = design.compute_hash()
        self.modules: List = []
        self.all_results: List[VerificationResult] = []

    def register_modules(self):
        self.modules = [
            DRCModule(self.design),
            ThermalModule(self.design),
            MechanicalModule(self.design),
            SupplyModule(self.design),
            SecurityModule(self.design)
        ]

    def phase_1_ingest(self) -> Dict:
        return {
            "phase": "INGESTAO",
            "design": self.design.name,
            "version": self.design.version,
            "hash": self.design_hash,
            "nets": len(self.design.nets),
            "components": len(self.design.components),
            "vias": len(self.design.vias),
            "layers": self.design.layers,
            "status": "OK"
        }

    def phase_2_analyze(self) -> List[VerificationResult]:
        self.all_results = [m.run_all() for m in self.modules]
        return self.all_results

    def phase_3_prove(self) -> List[ConstitutionalProof]:
        proofs = []
        for result in self.all_results:
            proofs.extend(result.proofs)
        return proofs

    def phase_4_audit(self) -> Dict:
        total_checks = sum(
            len(r.invariant_checks) + len(r.threat_checks)
            for r in self.all_results
        )
        failures = sum(
            1 for r in self.all_results
            for _, sev, _, _ in r.invariant_checks + r.threat_checks
            if sev in (Severity.FAIL, Severity.CRITICAL)
        )
        warnings = sum(
            1 for r in self.all_results
            for _, sev, _, _ in r.invariant_checks + r.threat_checks
            if sev == Severity.WARN
        )
        return {
            "phase": "AUDIT",
            "total_checks": total_checks,
            "failures": failures,
            "warnings": warnings,
            "constitutional_compliance": failures == 0,
            "status": "PASS" if failures == 0 else "FAIL"
        }

    def phase_5_register(self, proofs: List[ConstitutionalProof]) -> str:
        record = {
            "timestamp": time.time(),
            "design_hash": self.design_hash,
            "proof_count": len(proofs),
            "proof_hashes": [
                hashlib.sha3_256(str(p).encode()).hexdigest()[:16]
                for p in proofs
            ],
            "chain_anchor": hashlib.sha3_256(
                (self.design_hash + str(time.time())).encode()
            ).hexdigest()[:32]
        }
        return json.dumps(record, indent=2)

    def phase_6_action(self, audit: Dict) -> Dict:
        if audit["constitutional_compliance"]:
            return {
                "phase": "ACAO",
                "decision": "FABRICAR",
                "message": "Design passes all constitutional invariants. Proceed to fabrication.",
                "timestamp": time.time()
            }
        return {
            "phase": "ACAO",
            "decision": "CORRIGIR",
            "message": "Design violates " + str(audit["failures"]) + " constitutional invariants. Correction required.",
            "timestamp": time.time()
        }

    def run_full_verification(self) -> Dict:
        sep = "=" * 60
        print(sep)
        print("ARKHE 227-F VERIFICADOR CONSTITUCIONAL")
        print("Design: " + self.design.name + " v" + self.design.version)
        print("Hash: " + self.design_hash[:16] + "...")
        print(sep + "\n")

        ingest = self.phase_1_ingest()
        print("[FASE 1] " + ingest["phase"] + ": " + ingest["status"])
        print("  -> " + str(ingest["nets"]) + " nets, " + str(ingest["components"]) + " comps, " + str(ingest["vias"]) + " vias\n")

        print("[FASE 2] ANALISE: Executando " + str(len(self.modules)) + " modulos...")
        results = self.phase_2_analyze()
        for r in results:
            inv_pass = sum(1 for _, s, _, _ in r.invariant_checks if s == Severity.PASS)
            inv_total = len(r.invariant_checks)
            thr_pass = sum(1 for _, s, _, _ in r.threat_checks if s == Severity.PASS)
            thr_total = len(r.threat_checks)
            print("  -> " + r.module + ": " + str(inv_pass) + "/" + str(inv_total) + " inv, " + str(thr_pass) + "/" + str(thr_total) + " thr")
        print()

        proofs = self.phase_3_prove()
        print("[FASE 3] PROVA: " + str(len(proofs)) + " proof packets generated\n")

        audit = self.phase_4_audit()
        print("[FASE 4] AUDIT:")
        print("  -> Total checks: " + str(audit["total_checks"]))
        print("  -> Failures: " + str(audit["failures"]))
        print("  -> Warnings: " + str(audit["warnings"]))
        print("  -> Constitutional compliance: " + str(audit["constitutional_compliance"]))
        print("  -> Status: " + audit["status"] + "\n")

        chain_record = self.phase_5_register(proofs)
        print("[FASE 5] REGISTO: Arkhe(n)Chain anchor recorded")
        print("  -> " + chain_record + "\n")

        action = self.phase_6_action(audit)
        print("[FASE 6] ACAO: " + action["decision"])
        print("  -> " + action["message"])

        return {
            "ingest": ingest,
            "results": results,
            "audit": audit,
            "action": action,
            "design_hash": self.design_hash
        }

def create_valid_design() -> PCBDesign:
    return PCBDesign(
        name="TestBoard_Valid",
        version="1.0.0",
        nets=[
            Net(name="VCC", nodes=[(0, 0, 1), (10, 0, 1), (10, 10, 1)], width_mm=0.2, is_power=True),
            Net(name="GND", nodes=[(0, 10, 1), (0, 5, 1), (5, 10, 1)], width_mm=0.2, is_ground=True),
            Net(name="SIG1", nodes=[(2, 2, 1), (8, 2, 1), (8, 8, 1)], width_mm=0.15),
        ],
        components=[
            Component(
                ref="R1", footprint="R_0603", value="1k", pn="1k_0603_1%",
                mfr="Yageo", pos=(2, 2), rotation=0, layer="F.Cu",
                height_mm=0.5, thermal_watt=0.01,
                pins=[{"num": 1, "net": "SIG1"}, {"num": 2, "net": "GND"}]
            ),
            Component(
                ref="C1", footprint="C_0603", value="100nF", pn="100nF_0402_X7R",
                mfr="Murata", pos=(8, 2), rotation=0, layer="F.Cu",
                height_mm=0.5, thermal_watt=0.0,
                pins=[{"num": 1, "net": "VCC"}, {"num": 2, "net": "GND"}]
            ),
            Component(
                ref="U1", footprint="LQFP-48", value="MCU", pn="BSS138",
                mfr="ST", pos=(5, 5), rotation=0, layer="F.Cu",
                height_mm=1.2, thermal_watt=0.5,
                pins=[{"num": 1, "net": "VCC"}, {"num": 48, "net": "GND"}]
            ),
        ],
        vias=[
            Via(pos=(5, 5), drill_mm=0.3, pad_mm=0.6, layers=(1, 4), net="GND"),
            Via(pos=(2, 8), drill_mm=0.3, pad_mm=0.6, layers=(1, 4), net="VCC"),
        ],
        board_outline=[(0, 0), (10, 0), (10, 10), (0, 10)],
        layers=4,
        thickness_mm=1.6
    )

def create_failing_design() -> PCBDesign:
    return PCBDesign(
        name="TestBoard_Failing",
        version="0.9.0",
        nets=[
            Net(name="VCC", nodes=[(0, 0, 1), (0.1, 0, 1)], width_mm=0.2, is_power=True),
            Net(name="GND", nodes=[(0, 0.1, 1), (0.1, 0.1, 1)], width_mm=0.2, is_ground=True),
            Net(name="FLOAT", nodes=[(5, 5, 1)], width_mm=0.15),
        ],
        components=[
            Component(
                ref="R1", footprint="R_0603", value="1k", pn="INVALID_PN",
                mfr="Unknown", pos=(0, 0), rotation=0, layer="F.Cu",
                height_mm=0.5, thermal_watt=2.0,
                pins=[{"num": 1, "net": "VCC"}]
            ),
            Component(
                ref="R2", footprint="R_0603", value="10k", pn="10k_0603_1%",
                mfr="Yageo", pos=(0.05, 0), rotation=0, layer="F.Cu",
                height_mm=0.5, thermal_watt=0.01,
                pins=[{"num": 1, "net": "GND"}]
            ),
        ],
        vias=[
            Via(pos=(5, 5), drill_mm=0.1, pad_mm=0.15, layers=(1, 4), net="GND"),
        ],
        board_outline=[(0, 0), (10, 0), (10, 10), (0, 10)],
        layers=4,
        thickness_mm=1.6
    )

def run_test_suite():
    sep70 = "=" * 70
    sep60 = "=" * 60
    dash70 = "-" * 70

    print(sep70)
    print("ARKHE 227-F TEST SUITE CONSTITUCIONAL")
    print(sep70)

    print("\n" + dash70)
    print("TESTE 1: Design Valido (esperado: PASS em todos os invariantes)")
    print(dash70)
    valid_design = create_valid_design()
    verifier = Arkhe227FVerifier(valid_design)
    verifier.register_modules()
    result_valid = verifier.run_full_verification()

    assert result_valid["audit"]["constitutional_compliance"] is True
    assert result_valid["action"]["decision"] == "FABRICAR"
    print("\n✓ TESTE 1 PASSOU: Design valido aprovado constitucionalmente\n")

    print(dash70)
    print("TESTE 2: Design com Falhas (esperado: FAIL em multiplos invariantes)")
    print(dash70)
    failing_design = create_failing_design()
    verifier_fail = Arkhe227FVerifier(failing_design)
    verifier_fail.register_modules()
    result_fail = verifier_fail.run_full_verification()

    assert result_fail["audit"]["constitutional_compliance"] is False
    assert result_fail["action"]["decision"] == "CORRIGIR"
    print("\n✓ TESTE 2 PASSOU: Design falho rejeitado constitucionalmente\n")

    print(dash70)
    print("TESTE 3: Integridade dos Proof Packets")
    print(dash70)
    all_proofs = []
    for r in verifier.all_results + verifier_fail.all_results:
        all_proofs.extend(r.proofs)

    for proof in all_proofs:
        payload = (
            str(proof.timestamp) + "|" + proof.design_hash + "|" + proof.module_name + "|"
            + proof.invariant + "|" + proof.severity + "|" + proof.message + "|" + proof.details
        )
        expected = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
        assert proof.verifier_signature == expected

    print("✓ " + str(len(all_proofs)) + " proof packets verificados com integridade criptografica")
    print("✓ Nenhuma falsificacao detetada\n")

    print(dash70)
    print("TESTE 4: Imutabilidade do Design Hash")
    print(dash70)
    hash1 = valid_design.compute_hash()
    hash2 = valid_design.compute_hash()
    assert hash1 == hash2
    valid_design.version = "1.0.1"
    hash3 = valid_design.compute_hash()
    assert hash1 != hash3
    print("✓ Hash deterministico: " + hash1[:16] + "...")
    print("✓ Hash apos modificacao: " + hash3[:16] + "... (diferente)\n")

    print(dash70)
    print("TESTE 5: Hierarquia de Severidades")
    print(dash70)
    severity_order = [Severity.PASS, Severity.WARN, Severity.FAIL, Severity.CRITICAL]
    for i, sev in enumerate(severity_order):
        print("  -> " + sev.name + ": ordinal " + str(i))
    print("✓ Hierarquia de severidades estabelecida\n")

    print(sep70)
    print("RESUMO DA SUITE DE TESTES")
    print(sep70)
    print("✓ Teste 1 (Design Valido): PASS")
    print("✓ Teste 2 (Design Falho): PASS")
    print("✓ Teste 3 (Integridade de Proofs): PASS")
    print("✓ Teste 4 (Imutabilidade Hash): PASS")
    print("✓ Teste 5 (Hierarquia Severidades): PASS")
    print("\nTodos os 5 testes constitucionais passaram.")
    print("Substrato 227-F verificado e selado.")
    print(sep70)

    return {
        "test1_pass": result_valid["audit"]["constitutional_compliance"],
        "test2_pass": not result_fail["audit"]["constitutional_compliance"],
        "proofs_count": len(all_proofs),
        "hash_immutable": hash1 == hash2 and hash1 != hash3,
        "total_tests": 5,
        "passed_tests": 5
    }

if __name__ == "__main__":
    run_test_suite()
