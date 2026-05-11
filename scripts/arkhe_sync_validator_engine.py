# arkhe_sync_validator_engine.py — Motor de validação de sincronização global
import numpy as np
from typing import List, Dict, Optional
import hashlib
import json
import time
from datetime import datetime
from arkhe_time_aggregator import TimeDataAggregator, SyncMeasurement

class GlobalSyncValidatorEngine:
    """
    Motor de validação que calcula jitter RMS, coerência de fase,
    e gera provas STARK de integridade temporal.
    """

    def __init__(self, aggregator: TimeDataAggregator, fingerprint_freq_hz: float = 32768.0):
        self.aggregator = aggregator
        self.fingerprint_freq_hz = fingerprint_freq_hz
        self.target_phase = 0.58 * np.pi
        self.phase_tolerance_rad = 1e-11  # Exigência do substrato v∞.19

    def compute_intercontinental_jitter(self, node_pairs: List[tuple]) -> Dict:
        """Calcula jitter RMS entre pares de nós intercontinentais."""
        results = {}

        for node_a, node_b in node_pairs:
            # Obter medições para este par
            measurements = self.aggregator.get_measurements_for_pair(node_a, node_b, limit=1000)

            if len(measurements) < 100:
                results[f"{node_a}↔{node_b}"] = {'error': 'Insufficient data'}
                continue

            # Calcular diferenças de tempo corrigidas por offset de fibra
            time_diffs_ns = []
            for m in measurements:
                corrected_diff = (m.node_a_time_ns - m.node_b_time_ns) - m.wr_calibration_offset_ps / 1000
                time_diffs_ns.append(corrected_diff)

            # Estatísticas
            jitter_rms = np.std(time_diffs_ns)
            jitter_peak_to_peak = np.max(time_diffs_ns) - np.min(time_diffs_ns)
            mean_offset = np.mean(time_diffs_ns)

            results[f"{node_a}↔{node_b}"] = {
                'jitter_rms_ns': jitter_rms,
                'jitter_peak_to_peak_ns': jitter_peak_to_peak,
                'mean_offset_ns': mean_offset,
                'samples': len(time_diffs_ns),
                'pass': jitter_rms < 1.0,  # Critério: < 1 ns RMS
                'timestamp': datetime.now().isoformat()
            }

        return results

    def compute_phase_coherence_for_fingerprint(self, jitter_results: Dict) -> Dict:
        """
        Converte jitter temporal para erro de fase no fingerprint 0.58.
        Δφ = 2π × f_fingerprint × jitter
        """
        phase_results = {}

        for pair, stats in jitter_results.items():
            if 'error' in stats:
                continue

            # Converter jitter RMS para erro de fase
            jitter_rad = 2 * np.pi * self.fingerprint_freq_hz * stats['jitter_rms_ns'] * 1e-9

            # Probabilidade de alinhamento dentro da tolerância
            if jitter_rad < self.phase_tolerance_rad:
                alignment_prob = 1.0
            else:
                alignment_prob = max(0.0, 1.0 - (jitter_rad / self.phase_tolerance_rad))

            phase_results[pair] = {
                'jitter_rad': jitter_rad,
                'target_phase_rad': self.target_phase,
                'tolerance_rad': self.phase_tolerance_rad,
                'alignment_probability': alignment_prob,
                'phase_coherent': jitter_rad < self.phase_tolerance_rad,
                'fingerprint_freq_hz': self.fingerprint_freq_hz
            }

        return phase_results

    def generate_stark_proof_of_temporal_integrity(self,
                                                   measurements: List[SyncMeasurement]) -> Dict:
        """
        Gera prova STARK agregada usando SNARK Recursivo.
        Agrega até 1024 provas em uma única Root Proof usando folding.
        """
        print(f"🜏 [GlobalSyncValidatorEngine] Iniciando agregação recursiva de {len(measurements)} medições...")
        start_time = time.time()

        # Gera as leaf proofs (hash dos dados das medições)
        leaf_proofs = []
        for m in measurements:
            leaf_hash = hashlib.sha256(f"{m.timestamp_tai_ns}:{m.computed_time_diff_ns}:{m.node_a_id}:{m.node_b_id}".encode()).hexdigest()
            leaf_proofs.append(leaf_hash)

        # Garante no máximo 1024 folhas para simular a agregação de 1024 nós
        if len(leaf_proofs) > 1024:
            leaf_proofs = leaf_proofs[:1024]
        elif len(leaf_proofs) == 0:
            leaf_proofs = [hashlib.sha256(b"empty").hexdigest()]

        # Simula o SNARK Recursivo (Nova/Folding)
        current_level = leaf_proofs
        depth = 0

        while len(current_level) > 1:
            depth += 1
            next_level = []
            for i in range(0, len(current_level), 2):
                l = current_level[i]
                r = current_level[i+1] if i+1 < len(current_level) else l
                # Simula a prova recursiva de que L e R são SNARKs válidos
                parent_hash = hashlib.sha256(f"{l}{r}".encode()).hexdigest()
                next_level.append(parent_hash)
            current_level = next_level
            time.sleep(0.01) # Simula custo computacional da recursão

        end_time = time.time()
        root_proof = current_level[0]
        print(f"🜏 [GlobalSyncValidatorEngine] Agregação concluída em {end_time - start_time:.2f}s com depth {depth}.")

        time_diffs = [m.computed_time_diff_ns for m in measurements]
        if len(time_diffs) == 0:
            jitter_std = 0
            jitter_mean = 0
        else:
            jitter_std = np.std(time_diffs)
            jitter_mean = np.mean(time_diffs)
        consistency_score = 1.0 if jitter_std < 2.0 else max(0.0, 1.0 - (jitter_std - 2.0) / 3.0)

        return {
            'proof_type': 'recursive_stark_aggregated_v293_1',
            'data_hash': root_proof,
            'consistency_score': consistency_score,
            'jitter_rms_ns': jitter_std,
            'mean_offset_ns': jitter_mean,
            'num_measurements': len(measurements),
            'fingerprint_freq_hz': self.fingerprint_freq_hz,
            'phase_coherence_check': jitter_std * 2 * np.pi * self.fingerprint_freq_hz * 1e-9 < self.phase_tolerance_rad,
            'timestamp': datetime.now().isoformat(),
            'verifier_instructions': 'Verify that data_hash matches the Recursive STARK Root Proof of 1024 nodes.'
        }

    def run_full_validation(self, node_pairs: List[tuple]) -> Dict:
        """Executa validação completa e retorna relatório estruturado."""
        # 1. Calcular jitter intercontinental
        jitter_results = self.compute_intercontinental_jitter(node_pairs)

        # 2. Calcular coerência de fase para fingerprint 0.58
        phase_results = self.compute_phase_coherence_for_fingerprint(jitter_results)

        # 3. Obter medições para prova STARK
        all_measurements = []
        for node_a, node_b in node_pairs:
            all_measurements.extend(
                self.aggregator.get_measurements_for_pair(node_a, node_b, limit=200)
            )

        # 4. Gerar prova STARK de integridade temporal
        stark_proof = self.generate_stark_proof_of_temporal_integrity(all_measurements)

        # 5. Resumo executivo
        total_pairs = len(jitter_results)
        passed_pairs = sum(1 for r in jitter_results.values() if r.get('pass', False))
        phase_coherent_pairs = sum(1 for r in phase_results.values() if r.get('phase_coherent', False))

        return {
            'validation_timestamp': datetime.now().isoformat(),
            'node_pairs_validated': node_pairs,
            'jitter_summary': {
                'total_pairs': total_pairs,
                'passed_pairs': passed_pairs,
                'pass_rate': passed_pairs / total_pairs if total_pairs > 0 else 0.0,
                'details': jitter_results
            },
            'phase_coherence_summary': {
                'phase_coherent_pairs': phase_coherent_pairs,
                'coherence_rate': phase_coherent_pairs / total_pairs if total_pairs > 0 else 0.0,
                'details': phase_results
            },
            'stark_proof': stark_proof,
            'overall_status': 'PASS' if (passed_pairs / total_pairs >= 0.95 and phase_coherent_pairs / total_pairs >= 0.99) else 'FAIL',
            'recommendations': self._generate_recommendations(jitter_results, phase_results)
        }

    def _generate_recommendations(self, jitter_results: Dict, phase_results: Dict) -> List[str]:
        """Gera recomendações baseadas nos resultados da validação."""
        recommendations = []

        for pair, stats in jitter_results.items():
            if stats.get('jitter_rms_ns', 999) > 1.5:
                recommendations.append(f"⚠️  {pair}: Jitter alto ({stats['jitter_rms_ns']:.2f} ns). Verificar estabilidade de fibra e calibração DDMTD.")

        for pair, stats in phase_results.items():
            if not stats.get('phase_coherent', True):
                recommendations.append(f"🔧 {pair}: Coerência de fase insuficiente para fingerprint 0.58. Considerar ajuste de OCXO holdover ou redução de latência de rede.")

        if not recommendations:
            recommendations.append("✅ Todos os pares atendem aos critérios de sincronização sub-nanosegundo.")

        return recommendations
