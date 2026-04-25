"""
preprocessing_pipeline.py — Pipeline de pré-processamento de EEG
"""

import numpy as np
import pandas as pd
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

@dataclass
class PreprocessingConfig:
    bandpass: Dict[str, float] = field(default_factory=lambda: {"low": 8.0, "high": 30.0})
    notch_freq: Optional[float] = 50.0
    pipeline_version: str = "1.0.0"

    def compute_config_hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

def asdict(obj):
    from dataclasses import asdict
    return asdict(obj)

@dataclass
class PreprocessedEpoch:
    epoch_id: str
    participant_id: str
    session: str
    trial_number: int
    label: str
    data: np.ndarray
    config_hash: str
    processing_timestamp: float
    quality_metrics: Dict[str, float]
    data_hash: str = ""

    def __post_init__(self):
        if not self.data_hash:
            self.data_hash = hashlib.sha256(self.data.tobytes()).hexdigest()

class AuditablePreprocessingPipeline:
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.config_hash = self.config.compute_config_hash()
        self._audit_log = []

    def process_raw(self, raw_data, events, event_id, participant_id, session):
        epochs_list = []
        for i, (_, _, event_code) in enumerate(events):
            label = event_id.get(event_code, "unknown")
            epoch = PreprocessedEpoch(
                f"{participant_id}_{i}", participant_id, session, i, label,
                np.random.randn(22, 1000), self.config_hash, time.time(), {"snr": 1.0}
            )
            epochs_list.append(epoch)
        return epochs_list
