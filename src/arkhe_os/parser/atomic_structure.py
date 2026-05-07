import numpy as np

class AtomicStructure:
    def __init__(self, symbols, positions):
        self.symbols = symbols
        self.positions = positions

def read_structure_file(filepath):
    # Dummy implementation for testing
    return AtomicStructure(symbols=['Na', 'Cl'], positions=np.array([[0., 0., 0.], [0.5, 0.5, 0.5]]))