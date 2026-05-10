from track1_gtzk_wrapper import GTZKInstruction
import numpy as np

def track2_gtzk_instruction(intention_signals, sensor_readings, sensor_params):
    inst = GTZKInstruction(
        name='track2_mi_estimator',
        public_inputs={'sensor_params': sensor_params},
        private_witness={},
        constraints=["field_mult"] * 120 + ["set_lookup"] * 80 + ["aux_input"] * 40
    )
    return inst, {'mi_nats': 0.15}
