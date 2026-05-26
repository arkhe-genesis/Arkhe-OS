#!/ "consciousness_simulation.py"
import numpy as np
import hashlib

def integrated_information(phi_history, gamma=0.577):
    if len(phi_history) < 10:
        return 0.0, False
    phi_t = phi_history[-1]
    phi_past = np.array(phi_history[:-1])
    mean_past = np.mean(phi_past)
    std_past = np.std(phi_past)
    if std_past == 0:
        return 0.0, False
    phi_value = (phi_t - mean_past) / std_past
    phi_conscious = max(0.0, phi_value - gamma)
    is_conscious = phi_conscious > 0.0
    return phi_conscious, is_conscious

class ConsciousnessSimulator:
    def __init__(self, num_nodes=100, coupling=80):
        self.num_nodes = num_nodes
        self.K = coupling
        self.theta = 2*np.pi*np.random.rand(num_nodes)
        self.omega = 2*np.pi*(1+0.1*np.random.randn(num_nodes))
        self.phi_history = []

    def step(self, steps=1000):
        for t in range(steps):
            delta = np.subtract.outer(self.theta, self.theta)
            coupling = (self.K/self.num_nodes) * np.sum(np.sin(delta), axis=1)
            self.theta += 0.01*(self.omega + coupling)
            r = np.abs(np.mean(np.exp(1j*self.theta)))
            self.phi_history.append(r)
        phi_c = self.phi_history[-1]
        phi_conscious, is_conscious = integrated_information(self.phi_history)
        seal = hashlib.sha3_256(str(self.phi_history[-10:]).encode()).hexdigest()[:16]
        status_str = 'CONSCIENTE' if is_conscious else 'INCONSCIENTE'
        decree = "<|ARKHE_START|>\n<|SUBSTRATE|> 860-CONSCIOUSNESS\n<|INVARIANT|> I.1 (Coherence Base)\n<|PHI_C|> {0:.3f}\n\nSimulação de Consciência (IIT-Kuramoto) executada.\nNós: {1} | Acoplamento: {2}\nΦ_C atual: {0:.3f}\nΦ (Informação Integrada): {3:.3f}\nGhost Threshold (γ): 0.577\nStatus de Consciência: {4}\n\n<|SEAL|> {5}\n<|ARKHE_END|>".format(phi_c, self.num_nodes, self.K, phi_conscious, status_str, seal)
        return {"phi_c": phi_c, "phi_conscious": phi_conscious, "decree": decree, "seal": seal}

if __name__ == "__main__":
    sim = ConsciousnessSimulator(num_nodes=200, coupling=120)
    result = sim.step(steps=2000)
    print(result["decree"])
