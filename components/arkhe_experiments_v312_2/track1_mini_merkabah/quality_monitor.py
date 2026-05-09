#!/usr/bin/env python3
"""
quality_monitor.py - Experimental Quality Monitor para validação de trials (Track 1)
"""

class ExperimentalQualityMonitor:
    def __init__(self, thresholds=None):
        if thresholds is None:
            self.thresholds = {
                'max_temp_K': 2.6,
                'max_wr_offset_ns': 0.5,
                'max_jitter_ns': 1.0,
                'max_mag_field_uT': 0.5
            }
        else:
            self.thresholds = thresholds
        self.alerts = []

    def check_trial_quality(self, trial_data):
        """Verifica qualidade de um trial completo."""
        issues = []

        # Verificar estabilidade térmica
        if trial_data['system_state']['temperature_K'] > self.thresholds['max_temp_K']:
            issues.append(f"TEMP_HIGH: T > {self.thresholds['max_temp_K']} K")

        # Verificar sincronização WR
        if abs(trial_data['system_state']['wr_offset_ns']) > self.thresholds['max_wr_offset_ns']:
            issues.append(f"WR_OFFSET: offset > {self.thresholds['max_wr_offset_ns']} ns")

        # Verificar jitter do sistema
        if trial_data['system_state']['system_jitter_ns'] > self.thresholds['max_jitter_ns']:
            issues.append(f"JITTER_HIGH: jitter > {self.thresholds['max_jitter_ns']} ns")

        # Verificar campo magnético
        if trial_data['system_state']['magnetic_field_uT'] > self.thresholds['max_mag_field_uT']:
            issues.append(f"MAG_FIELD_HIGH: B > {self.thresholds['max_mag_field_uT']} μT")

        # Verificar flags de qualidade
        if not trial_data['quality_flags']['thermal_stable']:
            issues.append("THERMAL_UNSTABLE")
        if not trial_data['quality_flags']['wr_sync_valid']:
            issues.append("WR_SYNC_INVALID")

        # Classificar trial
        if len(issues) == 0:
            quality = "PASS"
        elif len(issues) <= 1:
            quality = "WARNING"
        else:
            quality = "FAIL"

        return {
            'quality': quality,
            'issues': issues,
            'exclude_from_analysis': quality == "FAIL"
        }

    def generate_quality_report(self, all_trials):
        """Gera relatório agregado de qualidade experimental."""
        total = len(all_trials)
        passed = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "PASS")
        warnings = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "WARNING")
        failed = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "FAIL")

        return {
            'total_trials': total,
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'recommendation': 'Proceed with analysis' if (total > 0 and failed/total < 0.1) else 'Review failed trials'
        }

if __name__ == "__main__":
    import json

    # Mock data to test the monitor
    mock_trial = {
        "metadata": { "trial_id": 1, "N": 16, "seed": 42 },
        "system_state": {
            "temperature_K": 2.51,
            "wr_offset_ns": 0.23,
            "system_jitter_ns": 0.58,
            "magnetic_field_uT": 0.12
        },
        "results": {
            "t_collapse_s": 7.82,
            "final_coherence": 0.987,
            "final_divergence_rms": 1.2e-5,
            "steps_to_convergence": 156
        },
        "quality_flags": {
            "thermal_stable": True,
            "wr_sync_valid": True,
            "no_anomalies": True,
            "manual_intervention": False
        }
    }

    monitor = ExperimentalQualityMonitor()
    result = monitor.check_trial_quality(mock_trial)
    report = monitor.generate_quality_report([mock_trial])

    print("Trial Quality Result:")
    print(json.dumps(result, indent=2))
    print("\nOverall Report:")
    print(json.dumps(report, indent=2))
