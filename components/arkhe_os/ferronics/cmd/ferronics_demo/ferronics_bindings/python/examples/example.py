// Basic usage of ferronic transceiver in Python
from arkhe_ferronics import new_ferron_transceiver, FerronConfig

config = FerronConfig(
    enable_quantum_mode=True,
    coherence_target=0.98
)
transceiver = new_ferron_transceiver("BaTiO3", config)
state, err = transceiver.encode_data(b"hello", 0)
if err is None:
    print(f"Encoded: amplitude={state.amplitude}, phase={state.phase}")
