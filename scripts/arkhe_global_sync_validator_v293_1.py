#!/usr/bin/env python3
"""
arkhe_global_sync_validator_v293_1.py
Substrato 293.1: Analisador e Validador de Sincronização Global.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List

FINGERPRINT_FREQ_HZ = 32768.0
TARGET_PHASE_RAD = 0.58 * np.pi
JITTER_THRESHOLD_NS = 1.0

class GlobalSyncValidator:
    def __init__(self, data_files: Dict[str, str]):
        """
        data_files: {'lisbon': 'sync_data/lisbon_sync.json',
                     'newyork': 'sync_data/newyork_sync.json', ...}
        """
        self.data = {}
        for node_id, path in data_files.items():
            with open(path) as f:
                self.data[node_id] = json.load(f)

    def _align_by_tai(self, node_a: str, node_b: str) -> np.ndarray:
        """Alinha medições de dois nós por timestamp TAI comum."""
        # Simplificação: interpolação para timestamps redondos
        times_a = np.array([m['timestamp_tai_ns'] for m in self.data[node_a]])
        times_b = np.array([m['timestamp_tai_ns'] for m in self.data[node_b]])
        common_t = np.intersect1d(times_a, times_b)
        diffs = []
        for t in common_t:
            v_a = next(m for m in self.data[node_a] if m['timestamp_tai_ns'] == t)
            v_b = next(m for m in self.data[node_b] if m['timestamp_tai_ns'] == t)
            corrected = (v_a['gnss_time_ns'] - v_b['gnss_time_ns']) - (v_a['wr_offset_ps'] + v_b['wr_offset_ps']) / 1000.0
            diffs.append(corrected)
        return np.array(diffs)

    def compute_jitter(self, pair: tuple) -> Dict:
        diffs = self._align_by_tai(pair[0], pair[1])
        if len(diffs) < 10:
            return {'error': 'Insufficient data'}
        jitter_rms = np.std(diffs)
        jitter_pp = np.ptp(diffs)
        return {
            'jitter_rms_ns': jitter_rms,
            'jitter_pp_ns': jitter_pp,
            'pass': jitter_rms < JITTER_THRESHOLD_NS,
            'samples': len(diffs)
        }

    def compute_phase_coherence(self, jitter_rms_ns: float) -> Dict:
        # Δφ = 2π × f × Δt
        phase_error_rad = 2 * np.pi * FINGERPRINT_FREQ_HZ * jitter_rms_ns * 1e-9
        tolerance = 1e-11
        return {
            'phase_error_rad': phase_error_rad,
            'tolerance_rad': tolerance,
            'coherent': phase_error_rad < tolerance
        }

    def run_full_analysis(self) -> str:
        pairs = [('lisbon', 'newyork'), ('lisbon', 'tokyo'), ('newyork', 'tokyo')]
        report = f"ARKHE SYNC VALIDATION REPORT\n{'='*40}\nDate: {datetime.now()}\n\n"
        for a, b in pairs:
            jitter = self.compute_jitter((a, b))
            if 'error' in jitter:
                report += f"{a}↔{b}: NO DATA\n"
                continue
            phase = self.compute_phase_coherence(jitter['jitter_rms_ns'])
            status = "✅ PASS" if jitter['pass'] and phase['coherent'] else "❌ FAIL"
            report += f"{a}↔{b}:\n"
            report += f"  Jitter RMS: {jitter['jitter_rms_ns']:.3f} ns (thresh: {JITTER_THRESHOLD_NS} ns)\n"
            report += f"  Phase Error: {phase['phase_error_rad']:.3e} rad (thresh: {phase['tolerance_rad']:.1e} rad)\n"
            report += f"  Result: {status}\n\n"

        print(report)
        with open("sync_validation_report.txt", "w") as f:
            f.write(report)
        return report

if __name__ == "__main__":
    # Após coletar dados de todos os nós, executar análise
    validator = GlobalSyncValidator({
        'lisbon': 'sync_data/lisbon_sync.json',
        'newyork': 'sync_data/newyork_sync.json',
        'tokyo': 'sync_data/tokyo_sync.json',
    })
    validator.run_full_analysis()
