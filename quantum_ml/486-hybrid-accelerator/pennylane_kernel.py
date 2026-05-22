# quantum_ml/486-hybrid-accelerator/pennylane_kernel.py
try:
    import pennylane as qml
    from pennylane import numpy as np
except ImportError:
    # Safe fallback if PennyLane is not available
    pass

class PennyLaneQuantumKernel:
    '''486-HYBRID-ACCELERATOR - Quantum kernel using PennyLane.'''

    def __init__(self, num_qubits: int = 4):
        self.num_qubits = num_qubits
        try:
            self.dev = qml.device("default.qubit", wires=num_qubits)
        except NameError:
            self.dev = None

    def feature_map(self, x):
        '''Encodes classical data into a quantum state.'''
        try:
            qml.AngleEmbedding(x, wires=range(self.num_qubits))
        except NameError:
            pass

    def compute_kernel(self, x1, x2):
        '''Computes the kernel value between two data points.'''
        if self.dev is None:
            # Fallback mock implementation
            import numpy as classical_np
            return float(classical_np.exp(-classical_np.linalg.norm(x1 - x2)**2))

        @qml.qnode(self.dev)
        def kernel_circuit(x1, x2):
            self.feature_map(x1)
            qml.adjoint(self.feature_map)(x2)
            return qml.probs(wires=range(self.num_qubits))

        # The probability of the all-zero state represents the overlap
        probs = kernel_circuit(x1, x2)
        return probs[0]
