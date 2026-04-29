# arkhe_clinical/acquire_optical_neural_rtd.py
"""
Aquisição sincronizada com correção de referencial terrestre dinâmico.
"""

import torch
import numpy as np
import time
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


class RTDOpticalNeuralAcquirer:
    """Orquestra aquisição com correção de referencial terrestre"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.rtd = TerrestrialReferenceFrame()
        self.optical_controller = self._init_optical_hardware()
        self.neural_recorder = self._init_neural_hardware()
        self.sync_module = self._init_synchronization()  # White Rabbit PTP

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
            # (se aplicável para alinhamento com referências astronômicas)
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
            time.sleep(self.config['trial_structure']['baseline_duration_s'])

            # Trigger com correção Sagnac aplicada
            trigger_ts = self.sync_module.send_marker(
                f"TRIAL_{idx}_START",
                sagnac_correction_ns=sagnac_corr*1e9
            )

            # Estimulação
            self.optical_controller.enable_beam(
                duration_s=self.config['trial_structure']['stimulation_duration_s']
            )

            # Pós-aquisição
            time.sleep(self.config['trial_structure']['post_duration_s'])

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

            time.sleep(self.config['trial_structure']['inter_trial_interval_s'])

        return trials

    def _load_config(self, path): return {}
    def _init_optical_hardware(self): return type('obj', (object,), {'set_vortex_params': lambda **kwargs: None, 'enable_beam': lambda **kwargs: None, 'measure_beam_metrics': lambda: {'sic_db': 0, 'rho': 0, 'eta': 0}})()
    def _init_neural_hardware(self): return type('obj', (object,), {'start_recording': lambda **kwargs: None, 'stop_recording': lambda: {'eeg': None, 'fnirs': None, 'psd_bands': {}, 'hbo_timecourse': np.array([])}})()
    def _init_synchronization(self): return type('obj', (object,), {'send_marker': lambda **kwargs: time.time()})()
    def _generate_param_grid(self): return [{'l_p': 1, 'm': 2, 'ratio': 0.7}]
    def _get_current_location(self): return 0.0, 0.0, 0.0
    def _compute_omega_neural(self, eeg, fnirs): return 0.0
    def _check_safety_limits(self, optical, neural): return True
