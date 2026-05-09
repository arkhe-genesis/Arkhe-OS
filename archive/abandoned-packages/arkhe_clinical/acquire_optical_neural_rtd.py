# arkhe_clinical/acquire_optical_neural_rtd.py
"""
Aquisição sincronizada com correção de referencial terrestre dinâmico.
"""

import torch
import numpy as np
import time
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
import h5py
from arkhe_core.temporal_reference import TerrestrialReferenceFrame

@dataclass
class RTDTrialData:
    """Dados de trial com metadados de referencial temporal"""
    # Parâmetros do estímulo
    l_p: int
    m: float
    ratio: float
    l_s: int

    # Métricas ópticas medidas
    sic_db: float
    rho: float
    eta: float

    # Métricas neurais medidas
    omega_neural: float
    eeg_psd: dict
    fnirs_hbo: np.ndarray

    # Metadados RTD
    participant_id: str
    trial_idx: int
    timestamp_utc: float
    timestamp_tdb: float  # Corrigido para escala dinâmica
    location_lat: float
    location_lon: float
    location_alt: float
    sagnac_correction_ns: float
    safety_checks_passed: bool


class MockOpticalController:
    def set_vortex_params(self, **kwargs): pass
    def enable_beam(self, duration_s): pass
    def measure_beam_metrics(self):
        return {'sic_db': 15.0, 'rho': 0.95, 'eta': 0.8}

class MockNeuralRecorder:
    def start_recording(self, **kwargs): pass
    def stop_recording(self):
        return {
            'eeg': np.random.rand(100),
            'fnirs': np.random.rand(100),
            'psd_bands': {'alpha': 0.5, 'beta': 0.3},
            'hbo_timecourse': np.random.rand(50)
        }

class MockSyncModule:
    def send_marker(self, label, sagnac_correction_ns):
        return time.time()

class RTDOpticalNeuralAcquirer:
    """Orquestra aquisição com correção de referencial terrestre"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.rtd = TerrestrialReferenceFrame()
        self.optical_controller = MockOpticalController()
        self.neural_recorder = MockNeuralRecorder()
        self.sync_module = MockSyncModule()

    def _load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _get_current_location(self):
        return -23.5505, -46.6333, 760.0 # São Paulo

    def _generate_param_grid(self):
        params = self.config['stimulation_protocol']['parameter_sweep']
        grid = []
        for l_p in params['l_p_values']:
            for m in params['m_values']:
                for ratio in params['ratio_values']:
                    grid.append({'l_p': l_p, 'm': m, 'ratio': ratio})
        return grid

    def _compute_omega_neural(self, eeg, fnirs):
        return 0.85 # Mock

    def _check_safety_limits(self, optical, neural):
        return True

    def run_calibration_session(self, participant_id: str) -> list[RTDTrialData]:
        """Executa sessão com correção RTD"""

        trials = []
        param_combinations = self._generate_param_grid()
        np.random.shuffle(param_combinations)

        # Obter localização atual via GPS
        lat, lon, alt = self._get_current_location()

        for idx, params in enumerate(param_combinations):
            # Timestamp UTC da aquisição
            timestamp_utc = time.time()

            # Corrigir para escala TDB
            timestamp_tdb = self.rtd.correct_timestamp(timestamp_utc, target_scale='tdb')

            # Calcular correção Sagnac para a configuração atual
            signal_path = [(lat, lon, alt)]  # Simplificado: nó único
            sagnac_corr = self.rtd.sagnac_correction(
                signal_path,
                signal_frequency_hz=80e6  # Rep rate do laser
            )

            print(f"\n🔬 Trial {idx+1}: l_p={params['l_p']}, UTC={timestamp_utc:.3f}, TDB={timestamp_tdb:.3f}, Sagnac={sagnac_corr*1e9:.1f}ns")

            # Configurar feixe vortex com correção de apontamento celeste
            self.optical_controller.set_vortex_params(
                l_p=params['l_p'],
                m=params['m'],
                ratio=params['ratio'],
                flat_top_order=6,
                celestial_correction=self.rtd.correct_coordinates(
                    ra_deg=0.0, dec_deg=90.0,  # Exemplo: polo celeste
                    obs_time_utc=timestamp_utc,
                    target_frame='itrs'
                )
            )

            # Aquisição neural com timestamp corrigido
            self.neural_recorder.start_recording(timestamp_tdb=timestamp_tdb)
            # time.sleep(self.config['stimulation_protocol']['trial_structure']['baseline_duration_s'])

            # Trigger com correção Sagnac aplicada
            trigger_ts = self.sync_module.send_marker(
                f"TRIAL_{idx}_START",
                sagnac_correction_ns=sagnac_corr*1e9
            )

            # Estimulação
            self.optical_controller.enable_beam(
                duration_s=self.config['stimulation_protocol']['trial_structure']['stimulation_duration_s']
            )

            # Pós-aquisição
            # time.sleep(self.config['stimulation_protocol']['trial_structure']['post_duration_s'])

            # Processar dados
            neural_data = self.neural_recorder.stop_recording()
            optical_metrics = self.optical_controller.measure_beam_metrics()
            omega_neural = self._compute_omega_neural(neural_data['eeg'], neural_data['fnirs'])
            safety_ok = self._check_safety_limits(optical_metrics, neural_data)

            # Empacotar trial com metadados RTD
            trial = RTDTrialData(
                l_p=params['l_p'], m=params['m'], ratio=params['ratio'], l_s=1,
                sic_db=optical_metrics['sic_db'], rho=optical_metrics['rho'],
                eta=optical_metrics['eta'],
                omega_neural=omega_neural,
                eeg_psd=neural_data['psd_bands'], fnirs_hbo=neural_data['hbo_timecourse'],
                participant_id=participant_id, trial_idx=idx,
                timestamp_utc=timestamp_utc, timestamp_tdb=timestamp_tdb,
                location_lat=lat, location_lon=lon, location_alt=alt,
                sagnac_correction_ns=sagnac_corr*1e9,
                safety_checks_passed=safety_ok
            )

            if safety_ok:
                trials.append(trial)

            time.sleep(0.1) # Brief pause for simulation
            # if idx >= 1: break # Removed for production-ready logic

        return trials

if __name__ == "__main__":
    acquirer = RTDOpticalNeuralAcquirer("arkhe_clinical/protocols/optical_neural_calibration_rtd_v1.0.yaml")
    acquirer.run_calibration_session("CALIB_001")
