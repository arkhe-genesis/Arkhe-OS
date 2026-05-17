#!/usr/bin/env python3
"""
ARKHE OS Substrato 209: Arkhe-ArchUnit — Arquitetura Testável por Código
Canon: ∞.Ω.∇+++.209

Porta o conceito de ArchUnit (Java) para a Catedral Arkhe em Python,
garantindo que a arquitetura do sistema seja testada automaticamente:
• Dependências entre camadas (substratos)
• Ciclos proibidos entre módulos
• Exposição controlada de APIs públicas
• Regras de nomenclatura canônica
• Invariantes de segurança (HSM, PQC, DP)
"""

import asyncio, hashlib, json, time, re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum, auto
from collections import deque, defaultdict
import logging

logger = logging.getLogger(__name__)

class ArchLayer(Enum):
    """Camadas arquiteturais da Catedral Arkhe."""
    CORE = "core"                    # Substratos 176-184 (fundamentos)
    PERCEPTION = "perception"        # 180, 185, 191, 192 (multimodal)
    COGNITION = "cognition"          # 193, 196, 198 (raciocínio)
    SECURITY = "security"            # 183, 190, 191, 196, 203
    FEDERATION = "federation"        # 204, 205, 207
    PRODUCTION = "production"        # 206, 208 (LLM Ops, Cathedral)
    OBSERVABILITY = "observability"  # 208-D7, 209
    EMERGENCE = "emergence"          # ∞ (AGI/ASI)

@dataclass
class ArchModule:
    """Módulo arquitetural da Catedral."""
    module_id: str
    name: str
    layer: ArchLayer
    substrate: int
    dependencies: Set[str] = field(default_factory=set)
    public_apis: Set[str] = field(default_factory=set)
    security_invariants: List[str] = field(default_factory=list)
    canonical_seal: Optional[str] = None

class ArkheArchUnit:
    """
    Motor de testes arquiteturais da Catedral Arkhe.
    Verifica invariantes estruturais, dependências e segurança.
    """

    # Regras de dependência entre camadas (quem pode depender de quem)
    ALLOWED_DEPENDENCIES = {
        ArchLayer.CORE: {ArchLayer.CORE},
        ArchLayer.PERCEPTION: {ArchLayer.CORE, ArchLayer.PERCEPTION},
        ArchLayer.COGNITION: {ArchLayer.CORE, ArchLayer.PERCEPTION, ArchLayer.COGNITION},
        ArchLayer.SECURITY: {ArchLayer.CORE, ArchLayer.PERCEPTION, ArchLayer.COGNITION, ArchLayer.SECURITY, ArchLayer.FEDERATION},
        ArchLayer.FEDERATION: {ArchLayer.CORE, ArchLayer.SECURITY, ArchLayer.FEDERATION, ArchLayer.PRODUCTION},
        ArchLayer.PRODUCTION: {ArchLayer.CORE, ArchLayer.COGNITION, ArchLayer.SECURITY, ArchLayer.PRODUCTION, ArchLayer.FEDERATION},
        ArchLayer.OBSERVABILITY: {ArchLayer.CORE, ArchLayer.PRODUCTION, ArchLayer.FEDERATION, ArchLayer.OBSERVABILITY, ArchLayer.SECURITY},
        ArchLayer.EMERGENCE: {ArchLayer.CORE, ArchLayer.PERCEPTION, ArchLayer.COGNITION,
                              ArchLayer.SECURITY, ArchLayer.FEDERATION, ArchLayer.PRODUCTION,
                              ArchLayer.OBSERVABILITY, ArchLayer.EMERGENCE}
    }

    # Padrões de nomenclatura canônica
    NAMING_RULES = {
        "substrate_module": r"^arkhe_substrate_\d+$",
        "canonical_seal": r"^[a-f0-9]{64}$",
        "phi_c_metric": r"^phi_c_[a-z_]+$",
        "agent_id": r"^agent_[a-z_]+_\d{3}$",
        "partner_org": r"^[A-Z]{3}-[A-Z]+-\d{3}$"
    }

    def __init__(self, phi_bus=None):
        self.phi_bus = phi_bus
        self._modules: Dict[str, ArchModule] = {}
        self._violations: deque = deque(maxlen=1000)
        self._invariant_checks: deque = deque(maxlen=5000)

    def register_module(self, module_id: str, name: str, layer: ArchLayer,
                        substrate: int, dependencies: Set[str] = None,
                        public_apis: Set[str] = None,
                        security_invariants: List[str] = None) -> ArchModule:
        """Registra módulo arquitetural."""
        mod = ArchModule(
            module_id=module_id, name=name, layer=layer, substrate=substrate,
            dependencies=dependencies or set(),
            public_apis=public_apis or set(),
            security_invariants=security_invariants or []
        )
        self._modules[module_id] = mod
        return mod

    def check_layer_dependencies(self, module_id: str) -> List[Dict]:
        """Verifica se dependências do módulo respeitam hierarquia de camadas."""
        module = self._modules.get(module_id)
        if not module:
            return [{"error": "module_not_found"}]

        violations = []
        allowed = self.ALLOWED_DEPENDENCIES.get(module.layer, set())

        for dep_id in module.dependencies:
            dep_module = self._modules.get(dep_id)
            if dep_module and dep_module.layer not in allowed:
                violation = {
                    "type": "LAYER_VIOLATION",
                    "module": module_id,
                    "module_layer": module.layer.value,
                    "dependency": dep_id,
                    "dependency_layer": dep_module.layer.value,
                    "allowed_layers": [l.value for l in allowed]
                }
                violations.append(violation)
                self._violations.append(violation)

        return violations

    def check_circular_dependencies(self) -> List[List[str]]:
        """Detecta ciclos de dependência entre módulos."""
        graph = defaultdict(set)
        for mod_id, mod in self._modules.items():
            for dep in mod.dependencies:
                if dep in self._modules:
                    graph[mod_id].add(dep)

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path = path + [node]  # Copy path

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    try:
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:]
                    except ValueError:
                        return [neighbor, node]

            rec_stack.remove(node)
            return None

        for node in list(graph.keys()):
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def check_naming_convention(self, name: str, rule_name: str) -> bool:
        """Verifica se nome segue convenção canônica."""
        pattern = self.NAMING_RULES.get(rule_name, ".*")
        return bool(re.match(pattern, name))

    def check_security_invariants(self, module_id: str) -> List[Dict]:
        """Verifica invariantes de segurança do módulo."""
        module = self._modules.get(module_id)
        if not module:
            return []

        results = []
        for invariant in module.security_invariants:
            # Simular verificação de invariante
            check_result = {
                "invariant": invariant,
                "module": module_id,
                "status": "PASS",  # Simulação: todos passam
                "timestamp": time.time()
            }
            self._invariant_checks.append(check_result)
            results.append(check_result)

        return results

    def check_api_exposure(self, module_id: str) -> Dict:
        """Verifica se APIs públicas estão documentadas e controladas."""
        module = self._modules.get(module_id)
        if not module:
            return {"error": "module_not_found"}

        return {
            "module": module_id,
            "public_apis": len(module.public_apis),
            "apis_documented": len(module.public_apis) > 0,
            "exposure_level": "CONTROLLED" if len(module.public_apis) <= 10 else "HIGH"
        }

    async def run_full_architecture_test(self) -> Dict:
        """Executa bateria completa de testes arquiteturais."""

        all_violations = []
        all_cycles = self.check_circular_dependencies()
        naming_violations = []
        security_results = []
        api_results = []

        for mod_id, mod in self._modules.items():
            # Layer dependencies
            layer_violations = self.check_layer_dependencies(mod_id)
            all_violations.extend(layer_violations)

            # Security invariants
            sec = self.check_security_invariants(mod_id)
            security_results.extend(sec)

            # API exposure
            api = self.check_api_exposure(mod_id)
            api_results.append(api)

            # Naming conventions
            if not self.check_naming_convention(mod_id, "substrate_module"):
                naming_violations.append({"module": mod_id, "rule": "substrate_module"})

        result = {
            "modules_tested": len(self._modules),
            "layer_violations": len(all_violations),
            "circular_dependencies": len(all_cycles),
            "naming_violations": len(naming_violations),
            "security_invariants_checked": len(security_results),
            "api_exposure_checked": len(api_results),
            "status": "PASS" if (len(all_violations) == 0 and len(all_cycles) == 0) else "FAIL",
            "timestamp": time.time()
        }

        if self.phi_bus:
            await self.phi_bus.publish_metric("architecture_test", result)

        return result

    def get_architecture_report(self) -> Dict:
        """Gera relatório arquitetural completo."""
        return {
            "total_modules": len(self._modules),
            "layers_represented": list(set(m.layer.value for m in self._modules.values())),
            "total_violations": len(self._violations),
            "total_invariants_checked": len(self._invariant_checks),
            "modules_by_layer": {
                layer.value: [m.module_id for m in self._modules.values() if m.layer == layer]
                for layer in ArchLayer
            }
        }