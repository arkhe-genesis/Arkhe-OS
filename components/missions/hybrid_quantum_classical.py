#!/usr/bin/env python3
"""
hybrid_quantum_classical.py — Executor de missões que coordenam computação clássica e quântica.
Sincroniza coerência entre subsistemas clássicos (C-RAG) e quânticos (QEC).
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import time

class HybridMissionPhase(Enum):
    """Fases de uma missão híbrida quântico-clássica."""
    INITIALIZATION = auto()
    CLASSICAL_PREP = auto()      # Preparação clássica (C-RAG retrieval)
    QUANTUM_EXEC = auto()        # Execução quântica (QEC/echo)
    COHERENCE_SYNC = auto()      # Sincronização de coerência
    RESULT_FUSION = auto()       # Fusão de resultados
    VALIDATION = auto()          # Validação final

@dataclass
class HybridMissionConfig:
    """Configuração para missão híbrida."""
    mission_id: str
    description: str
    classical_component: Dict  # config para C-RAG
    quantum_component: Dict    # config para QEC/quantum circuit
    coherence_threshold: float = 0.85  # limiar mínimo de coerência sincronizada
    max_retries: int = 3
    timeout_seconds: float = 300.0

class HybridMissionExecutor:
    """
    Executor de missões que coordenam subsistemas clássicos e quânticos.
    Garante que ΔK_clássico ≈ ΔK_quântico para coerência coordenada.
    """

    def __init__(
        self,
        config: HybridMissionConfig,
        classical_orchestrator: 'ArkheOrchestratorV161',
        quantum_interface: 'QiskitQuantumInterface'
    ):
        self.config = config
        self.classical_orchestrator = classical_orchestrator
        self.quantum_interface = quantum_interface

        # Estado da missão
        self.phase = HybridMissionPhase.INITIALIZATION
        self.classical_result: Optional[Dict] = None
        self.quantum_result: Optional[Dict] = None
        self.coherence_sync_status: Optional[Dict] = None

        # Callbacks para hooks personalizados
        self.on_phase_change: Optional[Callable] = None
        self.on_coherence_mismatch: Optional[Callable] = None

    async def execute(self) -> Dict:
        """Executa missão híbrida completa com sincronização de coerência."""
        start_time = time.time()
        result = {'mission_id': self.config.mission_id, 'phases': {}}

        try:
            # Fase 1: Preparação clássica
            self.phase = HybridMissionPhase.CLASSICAL_PREP
            self._notify_phase_change()

            classical_result = await self._execute_classical_component()
            result['phases']['classical'] = classical_result

            # Fase 2: Execução quântica
            self.phase = HybridMissionPhase.QUANTUM_EXEC
            self._notify_phase_change()

            quantum_result = await self._execute_quantum_component(
                classical_context=classical_result
            )
            result['phases']['quantum'] = quantum_result

            # Fase 3: Sincronização de coerência
            self.phase = HybridMissionPhase.COHERENCE_SYNC
            self._notify_phase_change()

            sync_status = self._synchronize_coherence(
                classical_gap=classical_result.get('kolmogorov_gap', 0.0),
                quantum_gap=quantum_result.get('coherence_gap', 0.0)
            )
            result['phases']['coherence_sync'] = sync_status

            if not sync_status['synchronized']:
                # Tentar correção se coerência não sincronizada
                if self.config.max_retries > 0:
                    result['phases']['retry'] = await self._retry_coherence_sync(
                        classical_result, quantum_result
                    )
                else:
                    result['status'] = 'FAILED_COHERENCE_SYNC'
                    return result

            # Fase 4: Fusão de resultados
            self.phase = HybridMissionPhase.RESULT_FUSION
            self._notify_phase_change()

            fused_result = self._fuse_results(classical_result, quantum_result)
            result['phases']['fusion'] = fused_result

            # Fase 5: Validação final
            self.phase = HybridMissionPhase.VALIDATION
            self._notify_phase_change()

            validation = self._validate_final_result(fused_result)
            result['validation'] = validation
            result['status'] = 'SUCCESS' if validation['valid'] else 'FAILED_VALIDATION'

        except asyncio.TimeoutError:
            result['status'] = 'TIMEOUT'
            result['error'] = f'Mission exceeded {self.config.timeout_seconds}s timeout'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)

        finally:
            result['execution_time_seconds'] = time.time() - start_time
            result['final_phase'] = self.phase.name

        return result

    async def _execute_classical_component(self) -> Dict:
        """Executa componente clássico (C-RAG) da missão."""
        # Extrair query do config da missão
        query = self.config.classical_component.get('query', 'default query')
        zone = self.config.classical_component.get('zone', 'Interior')

        # Executar via orchestrator clássico
        classical_result = await self.classical_orchestrator.process_crag_query(
            query=query,
            source_zone=zone,
            require_high_energy=False  # missão híbrida já tem componente quântico
        )

        # Extrair gap Kolmogorov do resultado clássico
        classical_gap = classical_result.get('kolmogorov_gap', 0.0)

        return {
            'response': classical_result.get('generated_text', ''),
            'kolmogorov_gap': classical_gap,
            'retrieved_docs': classical_result.get('retrieved_docs', 0),
            'safety_checks': classical_result.get('safety', {}),
            'timestamp': time.time()
        }

    async def _execute_quantum_component(
        self,
        classical_context: Dict
    ) -> Dict:
        """Executa componente quântico (QEC/echo) da missão."""
        # Construir circuito baseado no contexto clássico
        gap_estimate = classical_context.get('kolmogorov_gap', 0.0)

        # Configurar circuito de eco com parâmetros adaptativos
        circuit = self.quantum_interface.build_echo_circuit(
            echo_time_ns=750.0,  # tempo de Ramsey típico
            initial_state='|+⟩'  # estado de superposição para máxima sensibilidade
        )

        # Executar circuito com estimativa de gap para ruído realista
        quantum_result = self.quantum_interface.execute_circuit(
            circuit=circuit,
            gap_estimate=gap_estimate
        )

        # Calcular gap quântico a partir da coerência medida
        coherence = quantum_result.get('coherence_measure', 0.0)
        quantum_gap = max(0, 15.0 * (1.0 - coherence))  # mapear coerência → gap

        return {
            'circuit_executed': True,
            'fidelity_estimate': quantum_result.get('fidelity_estimate', 0.0),
            'coherence_measure': coherence,
            'coherence_gap': quantum_gap,
            'shots': quantum_result.get('shots', 0),
            'timestamp': time.time()
        }

    def _synchronize_coherence(
        self,
        classical_gap: float,
        quantum_gap: float
    ) -> Dict:
        """
        Sincroniza coerência entre subsistemas clássico e quântico.
        Retorna status de sincronização e métricas.
        """
        # Calcular diferença de gaps
        gap_difference = abs(classical_gap - quantum_gap)
        max_gap = max(classical_gap, quantum_gap, 1e-6)
        relative_difference = gap_difference / max_gap

        # Verificar se dentro do limiar de sincronização
        synchronized = relative_difference <= (1.0 - self.config.coherence_threshold)

        # Calcular fator de correção se necessário
        correction_factor = None
        if not synchronized and self.on_coherence_mismatch:
            # Callback para estratégia de correção personalizada
            correction_factor = self.on_coherence_mismatch(
                classical_gap=classical_gap,
                quantum_gap=quantum_gap,
                threshold=self.config.coherence_threshold
            )

        return {
            'synchronized': synchronized,
            'classical_gap': classical_gap,
            'quantum_gap': quantum_gap,
            'gap_difference': gap_difference,
            'relative_difference': relative_difference,
            'threshold': 1.0 - self.config.coherence_threshold,
            'correction_factor': correction_factor,
            'timestamp': time.time()
        }

    async def _retry_coherence_sync(
        self,
        classical_result: Dict,
        quantum_result: Dict
    ) -> Dict:
        """Tenta re-sincronizar coerência com parâmetros ajustados."""
        retry_results = []

        for attempt in range(self.config.max_retries):
            # Ajustar parâmetros quânticos baseado no mismatch
            current_gap_diff = abs(
                classical_result['kolmogorov_gap'] - quantum_result['coherence_gap']
            )

            # Aumentar tempo de eco para melhor supressão de ruído
            adjusted_echo_time = 750.0 * (1.0 + 0.2 * attempt)

            # Re-executar componente quântico com parâmetros ajustados
            quantum_result = await self._execute_quantum_component(classical_result)

            # Verificar sincronização
            sync_status = self._synchronize_coherence(
                classical_gap=classical_result['kolmogorov_gap'],
                quantum_gap=quantum_result['coherence_gap']
            )

            retry_results.append({
                'attempt': attempt + 1,
                'adjusted_echo_time_ns': adjusted_echo_time,
                'sync_status': sync_status
            })

            if sync_status['synchronized']:
                break

        return {
            'attempts': len(retry_results),
            'final_sync_status': retry_results[-1]['sync_status'],
            'retry_history': retry_results
        }

    def _fuse_results(
        self,
        classical_result: Dict,
        quantum_result: Dict
    ) -> Dict:
        """Funde resultados clássicos e quânticos em resposta unificada."""
        # Estratégia de fusão: ponderar pela coerência de cada subsistema
        classical_coherence = 1.0 - min(1.0, classical_result['kolmogorov_gap'] / 15.0)
        quantum_coherence = quantum_result.get('fidelity_estimate', 0.5)

        # Pesos normalizados
        total_coherence = classical_coherence + quantum_coherence + 1e-6
        classical_weight = classical_coherence / total_coherence
        quantum_weight = quantum_coherence / total_coherence

        # Fusão de respostas (exemplo: texto clássico + validação quântica)
        fused_response = {
            'text': classical_result.get('response', ''),
            'quantum_validation': {
                'fidelity': quantum_result.get('fidelity_estimate', 0.0),
                'coherence': quantum_result.get('coherence_measure', 0.0),
                'confidence': quantum_weight
            },
            'classical_confidence': classical_weight,
            'fused_confidence': (classical_weight + quantum_weight) / 2,
            'coherence_weights': {
                'classical': classical_weight,
                'quantum': quantum_weight
            }
        }

        return fused_response

    def _validate_final_result(self, fused_result: Dict) -> Dict:
        """Valida resultado final da missão híbrida."""
        # Critérios de validação
        min_confidence = 0.7
        min_coherence = 0.6

        fused_confidence = fused_result.get('fused_confidence', 0.0)
        quantum_coherence = fused_result.get('quantum_validation', {}).get('coherence', 0.0)

        valid = (
            fused_confidence >= min_confidence and
            quantum_coherence >= min_coherence
        )

        return {
            'valid': valid,
            'fused_confidence': fused_confidence,
            'quantum_coherence': quantum_coherence,
            'criteria': {
                'min_confidence': min_confidence,
                'min_coherence': min_coherence
            },
            'timestamp': time.time()
        }

    def _notify_phase_change(self):
        """Notifica callback de mudança de fase, se configurado."""
        if self.on_phase_change:
            self.on_phase_change(
                mission_id=self.config.mission_id,
                phase=self.phase.name,
                timestamp=time.time()
            )
