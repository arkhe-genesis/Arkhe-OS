from typing import List, Optional
import numpy as np
from enum import Enum

class NPUVendor(Enum):
    QUALCOMM_HEXAGON = "qualcomm_hexagon"
    INTEL_NPU = "intel_npu"
    UNKNOWN = "unknown"

class NPUInfo:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class NPUDirectMLConfig:
    def __init__(self, enable_power_optimization=False):
        self.enable_power_optimization = enable_power_optimization

class NPUDirectMLExecutor:
    def __init__(self):
        self.config = NPUDirectMLConfig(enable_power_optimization=True)

    def _enumerate_npus(self) -> List[NPUInfo]:
        return []

    async def _execute_directml_operator(
        self,
        compiled_op,
        input_tensor: np.ndarray,
        precision: str
    ) -> np.ndarray:
        return input_tensor

    def _select_npu(self, available: List[NPUInfo]) -> Optional[NPUInfo]:
        if available:
            return available[0]
        return None
