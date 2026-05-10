import numpy as np
from arkhe_os.temporal import FloquetParameters, CTCNode, CrossCTCSynchronizer

def test_cross_ctc_sync():
    shared_params = FloquetParameters(
        omega_d=2*np.pi*1e6,      # 1 MHz
        omega_R=2*np.pi*5e6,      # 5 MHz
        phase_offset=0.0
    )

    nodes = [
        CTCNode(ctc_id=1, natural_frequency=2*np.pi*1.1e6, gamma_0=1e3, phase_offset=0.01),
        CTCNode(ctc_id=2, natural_frequency=2*np.pi*1.0e6, gamma_0=1.2e3, phase_offset=-0.01),
        CTCNode(ctc_id=3, natural_frequency=2*np.pi*0.9e6, gamma_0=1.5e3, phase_offset=0.05),
    ]

    sync = CrossCTCSynchronizer(nodes, shared_params)

    operation_time = 10e-3 # 10 ms
    global_coherence = sync.global_coherence_metric(operation_time)
    fidelity = sync.synchronization_fidelity()

    assert global_coherence > 0.9
    assert fidelity > 0.99
