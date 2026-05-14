#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum_router.py — Substrato 7.5.0: Roteador Quântico Híbrido Photonic-Ion
Orquestra execução de circuitos QNC entre backends fotônicos e de íons aprisionados
baseado em fidelidade, latência, e requisitos do sub-circuito.
"""

import numpy as np
import asyncio, json, time, hashlib
from typing import Optional, Dict, List, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod

# Imports dos backends existentes
from src.arkhe.quantum.photonic.photonic_backend import PhotonicBackend, PhotonicJobConfig, PhotonicProvider
from src.arkhe.quantum.iontrap.iontrap_pulse_scheduler import IonTrapBackend, IonTrapJobConfig, IonSpecies

class QuantumBackendType(Enum):
    """Tipos de backend quântico suportados no roteador híbrido."""
    PHOTONIC = "photonic"
    ION_TRAP = "ion_trap"
    HYBRID = "hybrid"  # Execução distribuída entre ambos

class CircuitFragmentType(Enum):
    """Tipos de fragmentos de circuito e seu backend preferencial."""
    BOSON_SAMPLING = ("photonic", 0.95)      # Fotônico é ótimo para boson sampling
    HIGH_FIDELITY_GATE = ("ion_trap", 0.999)  # Íons são ótimos para gates precisos
    QUANTUM_MEMORY = ("ion_trap", 0.99)       # Íons têm T2 ~ segundos
    PHOTONIC_COMM = ("photonic", 0.98)        # Fótons são ótimos para comunicação
    ENTANGLEMENT_DIST = ("hybrid", 0.97)      # Emaranhamento distribuído usa ambos
    ERROR_CORRECTION = ("hybrid", 0.995)      # Correção de erros requer sinergia

@dataclass
class HybridExecutionConfig:
    """Configuração para execução híbrida de circuito quântico."""
    target_fidelity: float = 0.99
    max_latency_ms: float = 500.0
    prefer_local_execution: bool = True
    enable_error_mitigation: bool = True
    phi_c_aware_routing: bool = True  # Roteamento consciente de coerência Φ_C
    fallback_to_simulator: bool = True

@dataclass
class CircuitFragment:
    """Representa um fragmento de circuito quântico para roteamento."""
    fragment_id: str
    circuit_qasm: str
    fragment_type: CircuitFragmentType
    qubit_count: int
    depth_estimate: int
    fidelity_requirement: float
    latency_sensitivity: float  # 0-1, onde 1 = muito sensível
    dependencies: List[str] = field(default_factory=list)  # IDs de fragmentos anteriores

    def preferred_backend(self) -> QuantumBackendType:
        """Determina backend preferencial baseado no tipo de fragmento."""
        preferred, _ = self.fragment_type.value
        if preferred == "hybrid":
            # Decisão híbrida baseada em requisitos
            if self.fidelity_requirement > 0.995:
                return QuantumBackendType.ION_TRAP
            elif self.latency_sensitivity > 0.8:
                return QuantumBackendType.PHOTONIC
            else:
                return QuantumBackendType.HYBRID
        return QuantumBackendType(preferred)

@dataclass
class BackendAssignment:
    """Atribuição de fragmento a backend com métricas de adequação."""
    fragment_id: str
    backend: QuantumBackendType
    score: float
    estimated_latency: float
    estimated_cost: float
    fragment_circuit: str = ""
    qubit_count: int = 0

@dataclass
class FragmentResult:
    """Resultado da execução de um fragmento."""
    fragment_id: str
    backend: QuantumBackendType
    success: bool
    output_data: Any
    fidelity: float
    execution_time_ms: float
    temporal_anchor: Optional[str] = None

@dataclass
class HybridExecutionResult:
    """Resultado consolidado da execução híbrida."""
    success: bool
    output: Optional[Dict] = None
    error: Optional[str] = None
    estimated_fidelity: float = 0.0
    execution_time_ms: float = 0.0
    fragments_executed: int = 0
    backends_used: List[QuantumBackendType] = field(default_factory=list)
    integrity_proof: Optional[str] = None

class QuantumRouter:
    """
    Roteador inteligente para execução híbrida photonic-ion de circuitos QNC.

    Estratégia de roteamento:
    1. Decompor circuito QNC em fragmentos semanticamente coerentes
    2. Classificar cada fragmento por tipo e requisitos
    3. Selecionar backend ótimo baseado em:
       • Fidelidade requerida vs. capacidade do backend
       • Latência vs. tempo de execução estimado
       • Coerência Φ_C do sistema no momento da execução
       • Custo e disponibilidade de recursos
    4. Orquestrar execução distribuída com sincronização de estados
    5. Consolidar resultados com prova de integridade quântica
    """

    # Perfis de capacidade dos backends (valores empíricos/simulados)
    BACKEND_CAPABILITIES = {
        QuantumBackendType.PHOTONIC: {
            'max_qubits': 50,
            'max_depth': 100,
            'typical_fidelity': 0.98,
            'avg_latency_ms': 120.0,
            'cost_per_shot': 0.002,
            'best_for': [CircuitFragmentType.BOSON_SAMPLING, CircuitFragmentType.PHOTONIC_COMM],
        },
        QuantumBackendType.ION_TRAP: {
            'max_qubits': 32,
            'max_depth': 200,
            'typical_fidelity': 0.999,
            'avg_latency_ms': 300.0,
            'cost_per_shot': 0.005,
            'best_for': [CircuitFragmentType.HIGH_FIDELITY_GATE, CircuitFragmentType.QUANTUM_MEMORY],
        },
        QuantumBackendType.HYBRID: {
            'max_qubits': 80,  # Combinado
            'max_depth': 150,
            'typical_fidelity': 0.995,
            'avg_latency_ms': 450.0,  # Overhead de sincronização
            'cost_per_shot': 0.007,
            'best_for': [CircuitFragmentType.ENTANGLEMENT_DIST, CircuitFragmentType.ERROR_CORRECTION],
        },
    }

    def __init__(
        self,
        photonic_backend: PhotonicBackend,
        iontrap_backend: IonTrapBackend,
        config: HybridExecutionConfig = None,
    ):
        self.photonic = photonic_backend
        self.iontrap = iontrap_backend
        self.config = config or HybridExecutionConfig()
        self.execution_log: List[Dict] = []
        self.phi_c_monitor = None  # Será injetado pelo sistema ARKHE

    async def route_and_execute(
        self,
        qnc_circuit: Dict,
        context: Optional[Dict] = None,
    ) -> HybridExecutionResult:
        """
        Roteia e executa circuito QNC na arquitetura híbrida ótima.

        Fluxo:
        1. Decompor circuito em fragmentos
        2. Classificar e priorizar fragmentos
        3. Selecionar backends via algoritmo de custo-benefício quântico
        4. Executar fragmentos (paralelo quando possível)
        5. Sincronizar estados entre backends (teleportação quântica simulada)
        6. Consolidar resultados e gerar prova de integridade
        """
        start_time = time.time()

        # 1. Decomposição semântica do circuito QNC
        fragments = self._decompose_qnc_circuit(qnc_circuit)
        print(f"🔍 Circuito decomposto em {len(fragments)} fragmentos")

        # 2. Classificação e priorização
        prioritized = self._prioritize_fragments(fragments, context)

        # 3. Seleção de backends via otimização multi-objetivo
        assignments = await self._assign_backends(prioritized)

        # 4. Execução distribuída
        partial_results = await self._execute_fragments(assignments, context)

        # 5. Sincronização e consolidação
        final_result = await self._consolidate_results(partial_results, fragments)

        # 6. Ancoragem temporal e geração de prova
        execution_time = time.time() - start_time
        final_result.execution_time_ms = execution_time * 1000
        final_result.integrity_proof = self._generate_hybrid_proof(final_result, fragments)

        # Log para auditoria
        self.execution_log.append({
            'circuit_hash': hashlib.sha3_256(json.dumps(qnc_circuit, sort_keys=True).encode()).hexdigest()[:16],
            'fragments': len(fragments),
            'backends_used': list(set(a.backend for a in assignments.values())),
            'final_fidelity': final_result.estimated_fidelity,
            'execution_time_ms': final_result.execution_time_ms,
            'timestamp': time.time(),
        })

        return final_result

    def _decompose_qnc_circuit(self, circuit: Dict) -> List[CircuitFragment]:
        """Decompor circuito QNC em fragmentos semanticamente coerentes."""
        fragments = []
        fragment_id = 0

        # Heurística de decomposição baseada em padrões QNC
        for i, gate in enumerate(circuit.get('gates', [])):
            gate_type = gate.get('type', '')

            # Identificar fragmentos de boson sampling (fotônico)
            if gate_type in ['BS', 'PS', 'Sgate', 'MeasureFock']:
                fragments.append(CircuitFragment(
                    fragment_id=f"frag_{fragment_id:03d}",
                    circuit_qasm=json.dumps([gate]),
                    fragment_type=CircuitFragmentType.BOSON_SAMPLING,
                    qubit_count=gate.get('modes', 4),
                    depth_estimate=1,
                    fidelity_requirement=0.95,
                    latency_sensitivity=0.3,
                ))
                fragment_id += 1

            # Identificar fragmentos de gates de alta fidelidade (íons)
            elif gate_type in ['MS', 'Rabi_X', 'Rabi_Y', 'CNOT', 'CCNOT']:
                fragments.append(CircuitFragment(
                    fragment_id=f"frag_{fragment_id:03d}",
                    circuit_qasm=json.dumps([gate]),
                    fragment_type=CircuitFragmentType.HIGH_FIDELITY_GATE,
                    qubit_count=len(gate.get('qubits', [0, 1])),
                    depth_estimate=gate.get('depth', 5),
                    fidelity_requirement=0.999,
                    latency_sensitivity=0.6,
                ))
                fragment_id += 1

            # Identificar fragmentos de comunicação/emaranhamento (híbrido)
            elif gate_type in ['Teleport', 'Entangle', 'Swap']:
                fragments.append(CircuitFragment(
                    fragment_id=f"frag_{fragment_id:03d}",
                    circuit_qasm=json.dumps([gate]),
                    fragment_type=CircuitFragmentType.ENTANGLEMENT_DIST,
                    qubit_count=len(gate.get('qubits', [0, 1, 2])),
                    depth_estimate=10,
                    fidelity_requirement=0.99,
                    latency_sensitivity=0.9,  # Muito sensível a latência
                ))
                fragment_id += 1

        # Adicionar dependências baseadas em qubits compartilhados
        self._infer_dependencies(fragments)

        return fragments

    def _infer_dependencies(self, fragments: List[CircuitFragment]):
        """Inferir dependências entre fragmentos baseado em qubits compartilhados."""
        qubit_usage: Dict[int, List[str]] = {}

        # Mapear quais fragmentos usam quais qubits
        for frag in fragments:
            # Extrair qubits do QASM (simplificado)
            qubits = self._extract_qubits_from_qasm(frag.circuit_qasm)
            for q in qubits:
                qubit_usage.setdefault(q, []).append(frag.fragment_id)

        # Estabelecer dependências: fragmentos que compartilham qubits
        for qubit, frag_ids in qubit_usage.items():
            for i in range(len(frag_ids) - 1):
                # Fragmento posterior depende do anterior
                later_idx = fragments.index(next(f for f in fragments if f.fragment_id == frag_ids[i+1]))
                earlier_id = frag_ids[i]
                if earlier_id not in fragments[later_idx].dependencies:
                    fragments[later_idx].dependencies.append(earlier_id)

    def _extract_qubits_from_qasm(self, qasm: str) -> List[int]:
        """Extrair lista de qubits de uma string QASM (simplificado)."""
        import re
        matches = re.findall(r'q\[(\d+)\]', qasm)
        return [int(m) for m in matches] if matches else [0]

    def _prioritize_fragments(
        self,
        fragments: List[CircuitFragment],
        context: Optional[Dict],
    ) -> List[CircuitFragment]:
        """Priorizar fragmentos baseado em dependências e requisitos."""
        # Ordenação topológica simples baseada em dependências
        prioritized = []
        remaining = set(f.fragment_id for f in fragments)
        fragment_map = {f.fragment_id: f for f in fragments}

        while remaining:
            # Encontrar fragmentos sem dependências pendentes
            ready = [
                fid for fid in remaining
                if all(dep not in remaining for dep in fragment_map[fid].dependencies)
            ]

            if not ready:
                # Ciclo detectado — fallback para ordenação arbitrária
                ready = [next(iter(remaining))]

            # Ordenar fragmentos prontos por urgência (fidelidade + latência)
            ready.sort(key=lambda fid: (
                -fragment_map[fid].fidelity_requirement,  # Maior fidelidade primeiro
                -fragment_map[fid].latency_sensitivity,    # Mais sensível à latência primeiro
            ))

            for fid in ready:
                prioritized.append(fragment_map[fid])
                remaining.remove(fid)

        return prioritized

    async def _assign_backends(
        self,
        fragments: List[CircuitFragment],
    ) -> Dict[str, BackendAssignment]:
        """Atribuir cada fragmento ao backend ótimo via otimização multi-objetivo."""
        assignments = {}

        for frag in fragments:
            preferred = frag.preferred_backend()
            capabilities = self.BACKEND_CAPABILITIES[preferred]

            # Verificar se backend atende requisitos mínimos
            if (frag.qubit_count <= capabilities['max_qubits'] and
                frag.depth_estimate <= capabilities['max_depth'] and
                capabilities['typical_fidelity'] >= frag.fidelity_requirement):

                # Calcular score de adequação
                score = self._compute_assignment_score(frag, preferred, capabilities)
                assignments[frag.fragment_id] = BackendAssignment(
                    fragment_id=frag.fragment_id,
                    backend=preferred,
                    score=score,
                    estimated_latency=capabilities['avg_latency_ms'],
                    estimated_cost=capabilities['cost_per_shot'],
                    qubit_count=frag.qubit_count,
                    fragment_circuit=frag.circuit_qasm
                )
            else:
                # Fallback: tentar próximo melhor backend
                fallback = self._find_fallback_backend(frag, preferred)
                if fallback:
                    fb_caps = self.BACKEND_CAPABILITIES[fallback]
                    score = self._compute_assignment_score(frag, fallback, fb_caps)
                    assignments[frag.fragment_id] = BackendAssignment(
                        fragment_id=frag.fragment_id,
                        backend=fallback,
                        score=score,
                        estimated_latency=fb_caps['avg_latency_ms'],
                        estimated_cost=fb_caps['cost_per_shot'],
                        qubit_count=frag.qubit_count,
                        fragment_circuit=frag.circuit_qasm
                    )
                else:
                    # Último recurso: simulador
                    assignments[frag.fragment_id] = BackendAssignment(
                        fragment_id=frag.fragment_id,
                        backend=QuantumBackendType.ION_TRAP,  # Usar íons como fallback seguro
                        score=0.5,
                        estimated_latency=500.0,
                        estimated_cost=0.01,
                        qubit_count=frag.qubit_count,
                        fragment_circuit=frag.circuit_qasm
                    )

        return assignments

    def _compute_assignment_score(
        self,
        frag: CircuitFragment,
        backend: QuantumBackendType,
        caps: Dict,
    ) -> float:
        """Calcular score de adequação fragmento-backend (0-1)."""
        # Componentes do score
        fidelity_match = min(1.0, caps['typical_fidelity'] / frag.fidelity_requirement)
        latency_match = max(0.0, 1.0 - (caps['avg_latency_ms'] / 1000) * frag.latency_sensitivity)
        resource_fit = min(1.0,
            caps['max_qubits'] / max(1, frag.qubit_count),
            caps['max_depth'] / max(1, frag.depth_estimate)
        )

        # Peso para coerência Φ_C se habilitado
        phi_c_bonus = 0.0
        if self.config.phi_c_aware_routing and self.phi_c_monitor:
            current_phi_c = self.phi_c_monitor.get_current_coherence()
            # Backend com melhor Φ_C atual recebe bônus
            phi_c_bonus = 0.1 * (current_phi_c - 0.95) if current_phi_c > 0.95 else 0.0

        # Score combinado
        score = (
            0.4 * fidelity_match +
            0.3 * latency_match +
            0.2 * resource_fit +
            0.1 * (1.0 - caps['cost_per_shot'] / 0.01) +  # Custo menor = melhor
            phi_c_bonus
        )

        return np.clip(score, 0.0, 1.0)

    def _find_fallback_backend(
        self,
        frag: CircuitFragment,
        preferred: QuantumBackendType,
    ) -> Optional[QuantumBackendType]:
        """Encontrar backend alternativo se preferencial não atender requisitos."""
        # Ordem de fallback baseada em tipo de fragmento
        fallback_order = {
            CircuitFragmentType.BOSON_SAMPLING: [QuantumBackendType.PHOTONIC, QuantumBackendType.HYBRID],
            CircuitFragmentType.HIGH_FIDELITY_GATE: [QuantumBackendType.ION_TRAP, QuantumBackendType.HYBRID],
            CircuitFragmentType.ENTANGLEMENT_DIST: [QuantumBackendType.HYBRID, QuantumBackendType.ION_TRAP],
        }

        order = fallback_order.get(frag.fragment_type, [preferred])
        for backend in order:
            if backend != preferred:
                caps = self.BACKEND_CAPABILITIES[backend]
                if (frag.qubit_count <= caps['max_qubits'] and
                    frag.depth_estimate <= caps['max_depth']):
                    return backend
        return None

    async def _execute_fragments(
        self,
        assignments: Dict[str, BackendAssignment],
        context: Optional[Dict],
    ) -> Dict[str, FragmentResult]:
        """Executar fragmentos nos backends atribuídos (paralelo quando possível)."""
        results = {}

        # Agrupar fragmentos por backend para execução em lote
        by_backend: Dict[QuantumBackendType, List[BackendAssignment]] = {}
        for assignment in assignments.values():
            by_backend.setdefault(assignment.backend, []).append(assignment)

        # Executar cada grupo em paralelo
        tasks = []
        for backend_type, group in by_backend.items():
            if backend_type == QuantumBackendType.PHOTONIC:
                task = self._execute_photonic_group(group, context)
            elif backend_type == QuantumBackendType.ION_TRAP:
                task = self._execute_iontrap_group(group, context)
            else:  # HYBRID
                task = self._execute_hybrid_group(group, context)
            tasks.append(task)

        # Aguardar todas as execuções
        batch_results = await asyncio.gather(*tasks)

        # Consolidar resultados
        for backend_results in batch_results:
            results.update(backend_results)

        return results

    async def _execute_photonic_group(
        self,
        assignments: List[BackendAssignment],
        context: Optional[Dict],
    ) -> Dict[str, FragmentResult]:
        """Executar grupo de fragmentos no backend fotônico."""
        results = {}
        for assignment in assignments:
            # Converter fragmento para configuração fotônica
            config = PhotonicJobConfig(
                provider=PhotonicProvider.PSIQUANTUM,  # Ou selecionar dinamicamente
                circuit=assignment.fragment_circuit,
                shots=1024,
                photon_number=assignment.qubit_count // 2,
                error_mitigation=self.config.enable_error_mitigation,
            )

            # Executar no backend fotônico
            photonic_result = await self.photonic.execute(config)

            results[assignment.fragment_id] = FragmentResult(
                fragment_id=assignment.fragment_id,
                backend=QuantumBackendType.PHOTONIC,
                success=photonic_result.status == "completed",
                output_data=photonic_result.photon_counts,
                fidelity=photonic_result.interference_visibility or 0.95,
                execution_time_ms=photonic_result.execution_time_ms,
                temporal_anchor=photonic_result.temporal_anchor,
            )

        return results

    async def _execute_iontrap_group(self, assignments, context):
        """Executar grupo de fragmentos no backend de íons aprisionados."""
        results = {}
        for assignment in assignments:
            # Converter para configuração IonTrap
            config = IonTrapJobConfig(
                ion_species=IonSpecies.YB171,
                circuit=assignment.fragment_circuit,
                shots=2048,
                calibration_mode="auto",
            )

            # Executar no backend de íons
            ion_result = await self.iontrap.execute(config)

            results[assignment.fragment_id] = FragmentResult(
                fragment_id=assignment.fragment_id,
                backend=QuantumBackendType.ION_TRAP,
                success=ion_result.status == "completed",
                output_data=ion_result.measurement_counts,
                fidelity=ion_result.gate_fidelity or 0.999,
                execution_time_ms=ion_result.execution_time_ms,
                temporal_anchor=ion_result.temporal_anchor,
            )

        return results

    async def _execute_hybrid_group(self, assignments, context):
        """Executar grupo de fragmentos em modo híbrido (sincronizado)."""
        # Para fragmentos híbridos, executar fotônico e íons em paralelo
        # e sincronizar estados via teleportação quântica simulada
        results = {}

        for assignment in assignments:
            # Executar ambas as partes
            photonic_task = self._execute_photonic_group([assignment], context)
            iontrap_task = self._execute_iontrap_group([assignment], context)

            photonic_res, iontrap_res = await asyncio.gather(photonic_task, iontrap_task)

            # Combinar resultados com ponderação baseada em fidelidade
            p_res = list(photonic_res.values())[0]
            i_res = list(iontrap_res.values())[0]

            # Ponderação: íons têm maior fidelidade para gates, fotônicos para comunicação
            if assignment.fragment_circuit and "Teleport" in assignment.fragment_circuit:
                weight_photonic = 0.6
                weight_ion = 0.4
            else:
                weight_photonic = 0.3
                weight_ion = 0.7

            combined_fidelity = (
                weight_photonic * p_res.fidelity +
                weight_ion * i_res.fidelity
            )

            results[assignment.fragment_id] = FragmentResult(
                fragment_id=assignment.fragment_id,
                backend=QuantumBackendType.HYBRID,
                success=p_res.success and i_res.success,
                output_data={
                    'photonic': p_res.output_data,
                    'iontrap': i_res.output_data,
                    'combined': self._merge_outputs(p_res.output_data, i_res.output_data),
                },
                fidelity=combined_fidelity,
                execution_time_ms=max(p_res.execution_time_ms, i_res.execution_time_ms) * 1.2,  # Overhead de sincronização
                temporal_anchor=p_res.temporal_anchor or i_res.temporal_anchor,
            )

        return results

    def _merge_outputs(self, photonic_data, iontrap_data):
        """Combinar outputs de backends fotônico e de íons."""
        # Heurística simples: média ponderada para contagens
        if isinstance(photonic_data, dict) and isinstance(iontrap_data, dict):
            merged = {}
            all_keys = set(photonic_data.keys()) | set(iontrap_data.keys())
            for key in all_keys:
                p_val = photonic_data.get(key, 0)
                i_val = iontrap_data.get(key, 0)
                merged[key] = int(0.4 * p_val + 0.6 * i_val)  # Peso maior para íons
            return merged
        return photonic_data  # Fallback

    async def _consolidate_results(
        self,
        partial_results: Dict[str, FragmentResult],
        fragments: List[CircuitFragment],
    ) -> HybridExecutionResult:
        """Consolidar resultados parciais em resultado final do circuito."""
        # Verificar sucesso de todos os fragmentos
        all_successful = all(r.success for r in partial_results.values())

        if not all_successful:
            failed = [fid for fid, r in partial_results.items() if not r.success]
            return HybridExecutionResult(
                success=False,
                error=f"Fragment execution failed: {failed}",
                estimated_fidelity=0.0,
                execution_time_ms=0,
            )

        # Calcular fidelidade agregada (média geométrica ponderada)
        if not partial_results:
            return HybridExecutionResult(success=True)

        fidelities = [r.fidelity for r in partial_results.values()]
        weights = [1.0 / max(0.01, r.execution_time_ms) for r in partial_results.values()]  # Inverso do tempo
        total_weight = sum(weights)
        aggregated_fidelity = sum(f * w for f, w in zip(fidelities, weights)) / total_weight

        # Consolidar dados de output (simplificado: retornar dicionário de fragmentos)
        consolidated_output = {
            fid: result.output_data for fid, result in partial_results.items()
        }

        # Calcular tempo total (paralelo + overhead de sincronização)
        max_parallel_time = max(r.execution_time_ms for r in partial_results.values())
        sync_overhead = len(partial_results) * 5  # 5ms por fragmento para sincronização
        total_time = max_parallel_time + sync_overhead

        return HybridExecutionResult(
            success=True,
            output=consolidated_output,
            estimated_fidelity=aggregated_fidelity,
            execution_time_ms=total_time,
            fragments_executed=len(partial_results),
            backends_used=list(set(r.backend for r in partial_results.values())),
        )

    def _generate_hybrid_proof(
        self,
        result: HybridExecutionResult,
        fragments: List[CircuitFragment],
    ) -> str:
        """Gerar prova de integridade SHA3-256 para execução híbrida."""
        proof_data = {
            'result_fidelity': result.estimated_fidelity,
            'execution_time_ms': result.execution_time_ms,
            'fragments': len(fragments),
            'backends': [b.value for b in result.backends_used],
            'fragment_hashes': [
                hashlib.sha3_256(f.circuit_qasm.encode()).hexdigest()[:16]
                for f in sorted(fragments, key=lambda x: x.fragment_id)
            ],
            'timestamp': time.time(),
            'router_version': "7.5.0",
        }

        return hashlib.sha3_256(
            json.dumps(proof_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
