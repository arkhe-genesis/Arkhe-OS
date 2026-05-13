import numpy as np
from scipy.linalg import sqrtm

class FisherBuresManifold:
    def __init__(self, dim):
        self.dim = dim

    def geodesic(self, rho0, rho1, t):
        # Simplificação para teste
        return (1-t)*rho0 + t*rho1

class NaturalGradientFlow:
    def __init__(self, manifold):
        self.manifold = manifold

    def step(self, rho, grad, lr):
        rho_new = rho - lr * grad
        # Project back to density matrix
        rho_new = (rho_new + rho_new.conj().T) / 2
        eigvals, eigvecs = np.linalg.eigh(rho_new)
        eigvals = np.maximum(eigvals, 0)
        trace = np.sum(eigvals)
        if trace > 1e-10:
            eigvals /= trace
        else:
            eigvals = np.ones_like(eigvals) / self.manifold.dim
        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T
