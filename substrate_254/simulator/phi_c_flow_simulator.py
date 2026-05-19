#!/usr/bin/env python3
"""
ARKHE OS Substrate 254: Φ_C Flow Simulator Engine
Canon: ∞.Ω.∇+++.254.phi_c_simulator

Simulates data flow and Φ_C propagation through Arkhe-OS module graph
under various failure scenarios to assess systemic resilience.
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx
import matplotlib.pyplot as plt  # For visualization (optional)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# TIPOS CANÔNICOS DO SIMULADOR
# =============================================================================

class FailureType(Enum):
    """Tipos de falha simuláveis."""
    MODULE_CRASH = "module_crash"              # Module stops responding
    PHI_C_DEGRADATION = "phi_c_degradation"    # Module reports low coherence
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"  # Fails P1-P7 check
    NETWORK_PARTITION = "network_partition"    # Token Arkhe Bus disrupted
    TEMPORALCHAIN_UNAVAILABLE = "temporalchain_unavailable"  # Anchoring fails

@dataclass
class ModuleNode:
    """Representação de um módulo no grafo de simulação."""
    name: str
    layer: str  # 01_foundations, 02_hardware, etc.
    initial_phi_c: float  # Starting Φ_C value (0.0-1.0)
    current_phi_c: float  # Current simulated Φ_C
    constitutional_compliance: bool
    dependencies: List[str]  # Module names this module depends on
    dependents: List[str] = field(default_factory=list)  # Modules that depend on this
    phi_c_gate_threshold: float = 0.85  # Minimum Φ_C to accept inputs
    recovery_time_seconds: float = 30.0  # Estimated time to recover from failure

    def is_operational(self) -> bool:
        """Verifica se módulo está operacional."""
        return (self.current_phi_c >= self.phi_c_gate_threshold and
                self.constitutional_compliance)

@dataclass
class FailureEvent:
    """Evento de falha injetado na simulação."""
    failure_type: FailureType
    target_module: str
    start_time: float
    duration_seconds: float
    severity: float  # 0.0-1.0 impact magnitude
    description: str

@dataclass
class SimulationStep:
    """Estado do sistema em um passo de simulação."""
    time_step: int
    timestamp: float
    module_states: Dict[str, float]  # module_name -> current Φ_C
    composite_phi_c: float
    failed_modules: List[str]
    constitutional_violations: Dict[str, List[str]]  # module -> violated principles
    cascading_depth: int  # How many hops from original failure

@dataclass
class SimulationReport:
    """Relatório consolidado da simulação."""
    scenario_name: str
    failure_events: List[FailureEvent]
    total_steps: int
    final_composite_phi_c: float
    recovery_achieved: bool
    recovery_time_seconds: Optional[float]
    max_cascading_depth: int
    modules_permanently_failed: List[str]
    recommendations: List[str]
    temporal_chain_seal: Optional[str]
    simulation_timestamp: float

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "failure_events": [asdict(e) for e in self.failure_events]
        }

# =============================================================================
# MOTOR DE SIMULAÇÃO
# =============================================================================

class PhiCFlowSimulator:
    """Motor principal de simulação de fluxo de Φ_C."""

    # Default Φ_C propagation model parameters
    PROPAGATION_DECAY = 0.7  # How much Φ_C degradation propagates to dependents
    RECOVERY_RATE = 0.1      # Φ_C recovery per time step if no active failure
    CASCADE_THRESHOLD = 0.15  # Φ_C drop that triggers cascading to dependents

    def __init__(self, topology_file: str):
        """Inicializa simulador com topologia do sistema."""
        self.topology_file = Path(topology_file)
        self.modules: Dict[str, ModuleNode] = {}
        self.graph: nx.DiGraph = nx.DiGraph()
        self._load_topology()

    def _load_topology(self):
        """Carrega topologia do sistema a partir de arquivo."""
        if not self.topology_file.exists():
            # Generate default Arkhe-OS topology
            self._generate_default_topology()
            return

        with open(self.topology_file) as f:
            topology = json.load(f)

        for mod in topology.get("modules", []):
            node = ModuleNode(
                name=mod["name"],
                layer=mod["layer"],
                initial_phi_c=mod.get("initial_phi_c", 0.95),
                current_phi_c=mod.get("initial_phi_c", 0.95),
                constitutional_compliance=mod.get("constitutional_compliance", True),
                dependencies=mod.get("dependencies", []),
                phi_c_gate_threshold=mod.get("phi_c_gate_threshold", 0.85),
                recovery_time_seconds=mod.get("recovery_time_seconds", 30.0)
            )
            self.modules[node.name] = node
            self.graph.add_node(node.name, **asdict(node))

        # Build dependency edges
        for mod_name, mod in self.modules.items():
            for dep in mod.dependencies:
                if dep in self.modules:
                    self.graph.add_edge(dep, mod_name)
                    self.modules[dep].dependents.append(mod_name)

    def _generate_default_topology(self):
        """Gera topologia padrão do Arkhe-OS para simulação."""
        # Simplified Arkhe-OS module graph
        default_modules = [
            {"name": "token_arkhe_bus", "layer": "09_agents_multi_agent", "initial_phi_c": 0.98},
            {"name": "beaver_verifier", "layer": "07_formal_verification", "initial_phi_c": 0.99},
            {"name": "temporal_chain", "layer": "core", "initial_phi_c": 1.0},
            {"name": "phi_c_orchestration", "layer": "15_phi_c_orchestration", "initial_phi_c": 0.97},
            {"name": "hrm_238", "layer": "08_ai_ml", "initial_phi_c": 0.94},
            {"name": "agent_mesh", "layer": "09_agents_multi_agent", "initial_phi_c": 0.92},
            {"name": "ethereum_bridge", "layer": "10_blockchain_web3", "initial_phi_c": 0.90},
            {"name": "fips_crypto", "layer": "11_security_safety", "initial_phi_c": 0.96},
        ]

        default_deps = [
            ("token_arkhe_bus", "beaver_verifier"),
            ("token_arkhe_bus", "temporal_chain"),
            ("beaver_verifier", "phi_c_orchestration"),
            ("hrm_238", "token_arkhe_bus"),
            ("agent_mesh", "token_arkhe_bus"),
            ("ethereum_bridge", "token_arkhe_bus"),
            ("fips_crypto", "phi_c_orchestration"),
        ]

        for mod in default_modules:
            node = ModuleNode(
                name=mod["name"],
                layer=mod["layer"],
                initial_phi_c=mod["initial_phi_c"],
                current_phi_c=mod["initial_phi_c"],
                constitutional_compliance=True,
                dependencies=[]
            )
            self.modules[node.name] = node
            self.graph.add_node(node.name, **asdict(node))

        for src, dst in default_deps:
            if src in self.modules and dst in self.modules:
                self.graph.add_edge(src, dst)
                self.modules[src].dependents.append(dst)
                self.modules[dst].dependencies.append(src)

    def inject_failure(self, failure: FailureEvent):
        """Injeta evento de falha no sistema simulado."""
        if failure.target_module not in self.modules:
            raise ValueError(f"Module not found: {failure.target_module}")

        module = self.modules[failure.target_module]

        if failure.failure_type == FailureType.MODULE_CRASH:
            module.current_phi_c = 0.0
            module.constitutional_compliance = False

        elif failure.failure_type == FailureType.PHI_C_DEGRADATION:
            degradation = failure.severity * 0.5  # Max 0.5 drop
            module.current_phi_c = max(0.0, module.current_phi_c - degradation)

        elif failure.failure_type == FailureType.CONSTITUTIONAL_VIOLATION:
            module.constitutional_compliance = False
            # P1/P6 violations have higher Φ_C impact
            if failure.severity > 0.7:
                module.current_phi_c *= 0.7

        elif failure.failure_type == FailureType.NETWORK_PARTITION:
            # Partition affects Token Arkhe Bus and its dependents
            affected = [failure.target_module] + list(nx.descendants(self.graph, failure.target_module))
            for mod_name in affected:
                if mod_name in self.modules:
                    self.modules[mod_name].current_phi_c *= (1.0 - failure.severity * 0.3)

        elif failure.failure_type == FailureType.TEMPORALCHAIN_UNAVAILABLE:
            # Affects anchoring-dependent modules
            for mod in self.modules.values():
                if "temporal" in mod.layer or "anchor" in mod.name.lower():
                    mod.current_phi_c *= (1.0 - failure.severity * 0.2)

    def _propagate_phi_c_changes(self, time_step: int) -> Dict[str, float]:
        """Propaga mudanças de Φ_C através do grafo de dependências."""
        changes = {}

        for mod_name, module in self.modules.items():
            if not module.is_operational():
                # Propagate degradation to dependents
                for dependent_name in module.dependents:
                    dependent = self.modules.get(dependent_name)
                    if not dependent:
                        continue

                    # Calculate propagated degradation
                    degradation = (1.0 - module.current_phi_c) * self.PROPAGATION_DECAY

                    # Apply if above cascade threshold
                    if degradation > self.CASCADE_THRESHOLD:
                        old_phi_c = dependent.current_phi_c
                        dependent.current_phi_c = max(0.0, old_phi_c - degradation * 0.5)

                        # Check if dependent now violates its gate
                        if dependent.current_phi_c < dependent.phi_c_gate_threshold:
                            dependent.constitutional_compliance = False

                        changes[dependent_name] = dependent.current_phi_c - old_phi_c

        return changes

    def _apply_recovery(self, active_failures: List[FailureEvent], current_time: float):
        """Aplica recuperação natural de módulos não mais afetados por falhas."""
        for module in self.modules.values():
            # Skip modules with active failures
            if any(f.target_module == module.name and
                   f.start_time <= current_time < f.start_time + f.duration_seconds
                   for f in active_failures):
                continue

            # Natural recovery toward initial Φ_C
            if module.current_phi_c < module.initial_phi_c:
                recovery = (module.initial_phi_c - module.current_phi_c) * self.RECOVERY_RATE
                module.current_phi_c = min(module.initial_phi_c, module.current_phi_c + recovery)

            # Restore constitutional compliance if Φ_C recovered
            if module.current_phi_c >= module.phi_c_gate_threshold:
                module.constitutional_compliance = True

    def _calculate_composite_phi_c(self) -> float:
        """Calcula Φ_C composto do sistema."""
        if not self.modules:
            return 0.0

        # Weighted average: core layers have higher weight
        weights = {
            "core": 2.0,
            "15_phi_c_orchestration": 1.8,
            "07_formal_verification": 1.5,
            "11_security_safety": 1.5,
            "09_agents_multi_agent": 1.2,
            "default": 1.0
        }

        total_weight = 0
        weighted_sum = 0

        for module in self.modules.values():
            weight = weights.get(module.layer, weights["default"])
            if module.is_operational():
                weighted_sum += module.current_phi_c * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def run_simulation(self, failures: List[FailureEvent],
                      time_steps: int = 100, step_duration_seconds: float = 1.0) -> SimulationReport:
        """Executa simulação completa com cenários de falha."""
        logger.info(f"🧪 Starting Φ_C flow simulation: {len(failures)} failures, {time_steps} steps")

        simulation_steps: List[SimulationStep] = []
        max_cascading_depth = 0
        recovery_time = None

        for step in range(time_steps):
            current_time = step * step_duration_seconds

            # Apply active failures
            active_failures = [f for f in failures
                             if f.start_time <= current_time < f.start_time + f.duration_seconds]
            for failure in active_failures:
                if current_time == failure.start_time:  # Apply only at start
                    self.inject_failure(failure)

            # Propagate Φ_C changes
            self._propagate_phi_c_changes(step)

            # Apply recovery
            self._apply_recovery(active_failures, current_time)

            # Record step state
            composite_phi_c = self._calculate_composite_phi_c()
            failed_modules = [name for name, mod in self.modules.items() if not mod.is_operational()]

            # Calculate cascading depth (BFS from failed modules)
            cascading_depth = 0
            if failed_modules:
                visited = set(failed_modules)
                queue = [(name, 0) for name in failed_modules]
                while queue:
                    mod_name, depth = queue.pop(0)
                    cascading_depth = max(cascading_depth, depth)
                    for dependent in self.modules[mod_name].dependents:
                        if dependent not in visited and not self.modules[dependent].is_operational():
                            visited.add(dependent)
                            queue.append((dependent, depth + 1))

            max_cascading_depth = max(max_cascading_depth, cascading_depth)

            step_record = SimulationStep(
                time_step=step,
                timestamp=current_time,
                module_states={name: mod.current_phi_c for name, mod in self.modules.items()},
                composite_phi_c=composite_phi_c,
                failed_modules=failed_modules,
                constitutional_violations={
                    name: ["P1", "P6"] for name, mod in self.modules.items()
                    if not mod.constitutional_compliance
                },
                cascading_depth=cascading_depth
            )
            simulation_steps.append(step_record)

            # Check for recovery
            if recovery_time is None and composite_phi_c >= 0.90 and not failed_modules:
                recovery_time = current_time

        # Generate recommendations
        recommendations = self._generate_recommendations(simulation_steps, failures)

        # Generate temporal seal
        report_payload = {
            "scenario": "simulated",
            "failures": len(failures),
            "final_phi_c": simulation_steps[-1].composite_phi_c if simulation_steps else 0,
            "recovered": recovery_time is not None,
            "timestamp": time.time()
        }
        temporal_seal = hashlib.sha3_256(
            json.dumps(report_payload, sort_keys=True).encode()
        ).hexdigest()

        return SimulationReport(
            scenario_name="simulated_scenario",
            failure_events=failures,
            total_steps=time_steps,
            final_composite_phi_c=simulation_steps[-1].composite_phi_c if simulation_steps else 0,
            recovery_achieved=recovery_time is not None,
            recovery_time_seconds=recovery_time,
            max_cascading_depth=max_cascading_depth,
            modules_permanently_failed=[name for name, mod in self.modules.items()
                                       if not mod.is_operational() and mod.current_phi_c < 0.5],
            recommendations=recommendations,
            temporal_chain_seal=temporal_seal,
            simulation_timestamp=time.time()
        )

    def _generate_recommendations(self, steps: List[SimulationStep],
                                 failures: List[FailureEvent]) -> List[str]:
        """Gera recomendações baseadas nos resultados da simulação."""
        recommendations = []

        # Check for single points of failure
        for mod_name, module in self.modules.items():
            if len(module.dependents) >= 3 and module.layer in ["core", "15_phi_c_orchestration"]:
                recommendations.append(
                    f"Consider adding redundancy for {mod_name} (P2): {len(module.dependents)} dependents"
                )

        # Check Φ_C gate thresholds
        low_threshold_modules = [name for name, mod in self.modules.items()
                               if mod.phi_c_gate_threshold < 0.80]
        if low_threshold_modules:
            recommendations.append(
                f"Review Φ_C gate thresholds for: {', '.join(low_threshold_modules)} (may allow degraded inputs)"
            )

        # Recovery time analysis
        if any(f.duration_seconds > 60 for f in failures):
            recommendations.append(
                "Implement auto-healing for long-duration failures (>60s) to reduce recovery time"
            )

        # Constitutional violation patterns
        p1_violations = sum(1 for step in steps
                          for violations in step.constitutional_violations.values()
                          if "P1" in violations)
        if p1_violations > len(steps) * 0.3:
            recommendations.append(
                "High P1 violation rate: strengthen formal verification integration (Lean Bridge, BEAVER)"
            )

        return recommendations if recommendations else ["System demonstrates good resilience under simulated failures"]

    def visualize_simulation(self, report: SimulationReport, output_file: str = "simulation_graph.png"):
        """Gera visualização do grafo de simulação com estados finais."""
        try:
            plt.figure(figsize=(12, 8))

            # Color nodes by Φ_C
            node_colors = [
                self.modules[name].current_phi_c
                for name in self.graph.nodes()
            ]

            pos = nx.spring_layout(self.graph, k=2, iterations=50)
            nx.draw(self.graph, pos,
                   node_color=node_colors,
                   cmap=plt.cm.RdYlGn,
                   with_labels=True,
                   node_size=2000,
                   font_size=8,
                   edge_color='gray',
                   arrows=True)

            plt.title(f"Φ_C Flow Simulation: {report.scenario_name}\nFinal Composite Φ_C: {report.final_composite_phi_c:.3f}")
            plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn), label="Module Φ_C")
            plt.tight_layout()
            plt.savefig(output_file, dpi=150)
            logger.info(f"📊 Visualization saved to {output_file}")

        except Exception as e:
            logger.warning(f"⚠️ Visualization failed: {e}")

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARKHE Φ_C Flow Simulator")
    parser.add_argument("--topology", default="arkhe_topology.json", help="System topology file")
    parser.add_argument("--scenario", choices=["single_failure", "cascade", "network_partition", "custom"],
                       default="single_failure", help="Failure scenario preset")
    parser.add_argument("--steps", type=int, default=100, help="Simulation time steps")
    parser.add_argument("--output", help="Output report file (JSON)")
    parser.add_argument("--visualize", action="store_true", help="Generate visualization")

    args = parser.parse_args()

    simulator = PhiCFlowSimulator(args.topology)

    # Generate failure scenario
    failures = []
    if args.scenario == "single_failure":
        failures.append(FailureEvent(
            failure_type=FailureType.PHI_C_DEGRADATION,
            target_module="token_arkhe_bus",
            start_time=10.0,
            duration_seconds=30.0,
            severity=0.8,
            description="Simulated Φ_C degradation in Token Arkhe Bus"
        ))
    elif args.scenario == "cascade":
        failures.extend([
            FailureEvent(FailureType.MODULE_CRASH, "beaver_verifier", 5.0, 20.0, 1.0, "Verifier crash"),
            FailureEvent(FailureType.PHI_C_DEGRADATION, "phi_c_orchestration", 15.0, 40.0, 0.6, "Orchestration degradation"),
        ])
    elif args.scenario == "network_partition":
        failures.append(FailureEvent(
            failure_type=FailureType.NETWORK_PARTITION,
            target_module="token_arkhe_bus",
            start_time=10.0,
            duration_seconds=60.0,
            severity=0.9,
            description="Network partition affecting Token Arkhe Bus"
        ))

    # Run simulation
    report = simulator.run_simulation(failures, time_steps=args.steps)

    # Output report
    print(f"\n🧪 Φ_C Flow Simulation Report")
    print(f"   Scenario: {report.scenario_name}")
    print(f"   Final Composite Φ_C: {report.final_composite_phi_c:.3f}")
    print(f"   Recovery Achieved: {'✅ Yes' if report.recovery_achieved else '❌ No'}")
    if report.recovery_time_seconds:
        print(f"   Recovery Time: {report.recovery_time_seconds:.1f}s")
    print(f"   Max Cascading Depth: {report.max_cascading_depth}")
    print(f"   Permanently Failed Modules: {len(report.modules_permanently_failed)}")

    if report.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   • {rec}")

    # Visualization
    if args.visualize:
        simulator.visualize_simulation(report)

    # Save report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n💾 Report saved to {args.output}")

    # TemporalChain anchor
    if report.temporal_chain_seal:
        print(f"🔗 TemporalChain Seal: {report.temporal_chain_seal[:32]}...")

if __name__ == "__main__":
    main()

# Enforce Gap Soberano (P3 compliance)
PHI_C_CAP = 1.0
def inject_novelty():
    """Generates residual_flux for novelty injection."""
    pass
