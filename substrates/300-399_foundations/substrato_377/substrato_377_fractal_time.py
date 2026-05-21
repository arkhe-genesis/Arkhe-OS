import math
import random
import time
import hashlib

# Canonical Constants
PHI_GOLDEN = 1.618033988749895
GHOST = 0.5773502691896257
LOOPSEAL = 0.3490658503988659
GAP_SOVEREIGN = 0.9999

class FractalWaveEngine:
    def __init__(self, n_nodes=59, p_edge=0.3):
        self.n_nodes = n_nodes
        self.p_edge = p_edge

    def simulate_fractal_wave_consensus(self, max_iter=20):
        # Topologia
        random.seed(377)
        adj = [[0.0 for _ in range(self.n_nodes)] for _ in range(self.n_nodes)]
        for i in range(self.n_nodes):
            for j in range(i+1, self.n_nodes):
                if random.random() < self.p_edge:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0

        # Ensure connected
        for i in range(self.n_nodes - 1):
             adj[i][i+1] = 1.0
             adj[i+1][i] = 1.0

        # Opiniões iniciais (Φ_C locais)
        opinions = [random.random() for _ in range(self.n_nodes)]
        history = [list(opinions)]

        for wave in range(max_iter):
            new_opinions = [0.0] * self.n_nodes
            # Cada nó emite uma wavelet que se propaga para os vizinhos
            for i in range(self.n_nodes):
                for j in range(self.n_nodes):
                    if adj[i][j] > 0:
                        # Wavelet de Huygens: atenuação com a distância = 1 (vizinho direto)
                        distance = 1.0
                        attenuation = math.exp(-distance / (wave + 1))  # escala temporal
                        new_opinions[j] += opinions[i] * attenuation
            # Normalizar (interferência construtiva / número de contribuições)
            max_opinion = max(new_opinions)
            if max_opinion > 0:
                 new_opinions = [o / max_opinion for o in new_opinions]
            opinions = new_opinions
            history.append(list(opinions))

            # Critério de convergência
            mean_opinion = sum(opinions) / len(opinions)
            std_opinion = math.sqrt(sum((o - mean_opinion)**2 for o in opinions) / len(opinions))
            if std_opinion < 0.05:
                break

        mean_final = sum(opinions) / len(opinions)
        std_final = math.sqrt(sum((o - mean_final)**2 for o in opinions) / len(opinions))
        return {
            "waves_to_converge": len(history),
            "final_mean": mean_final,
            "final_std": std_final,
            "history": history
        }

class AeneidFractalClock:
    def __init__(self, validator_id, peers):
        self.id = validator_id
        self.state = {"phi_c": 0.88, "merkle_root": None}
        self.peers = peers
        self.wavelet_history = []

    def emit_state_wavelet(self):
        """Emite o estado atual como uma wavelet de Huygens."""
        wavelet = {
            "validator": self.id,
            "state_hash": hashlib.sha256(str(self.state).encode()).hexdigest(),
            "phi_c": self.state["phi_c"],
            "timestamp": time.time(),
            "amplitude": 1.0,
            "phase": random.random() * 2 * math.pi
        }
        for peer in self.peers:
            peer.receive_wavelet(wavelet)

    def receive_wavelet(self, wavelet):
        """Recebe uma wavelet e agrega ao estado local."""
        self.wavelet_history.append(wavelet)
        # Agregar apenas wavelets recentes (últimos 2 segundos)
        recent = [w for w in self.wavelet_history if time.time() - w["timestamp"] < 2.0]
        # Contar concordância de estado
        state_votes = {}
        for w in recent:
            state_votes[w["state_hash"]] = state_votes.get(w["state_hash"], 0) + 1
        # Se um estado tem supermaioria (76%), confirmar
        total = len(self.peers) + 1
        for state_hash, votes in state_votes.items():
            if votes / total >= 0.76:
                self.confirm_state(state_hash)

    def confirm_state(self, state_hash):
        """Confirma o estado e ancora na TemporalChain."""
        # Ancorar Merkle root da TemporalChain
        self.state["merkle_root"] = state_hash

class DistributedFractalFFT:
    def fractal_fft_distributed(self, signal, node_id, all_nodes):
        """Executa uma etapa da Fractal FFT distribuída em um nó."""
        n_total = len(signal)
        # Cada nó é responsável por um segmento do sinal
        segment_size = n_total // len(all_nodes)
        local_segment = signal[node_id * segment_size : (node_id + 1) * segment_size]

        # FFT local (zero-padded para a potência de 2 mais próxima)
        # Para evitar numpy, implementamos DFT local manual se N for pequeno
        N = segment_size
        local_fft = [0j] * N
        for k in range(N):
            val = 0j
            for n in range(N):
                angle = -2 * math.pi * k * n / N
                val += local_segment[n] * complex(math.cos(angle), math.sin(angle))
            local_fft[k] = val

        # Propagar coeficientes como wavelets para vizinhos na rede borboleta
        num_steps = int(math.log2(len(all_nodes))) if len(all_nodes) > 0 else 0
        for step in range(num_steps):
            partner = node_id ^ (1 << step)
            if partner < len(all_nodes):
                # combinar arrays locais
                combined = [0j] * (N * 2)
                for i in range(N):
                    combined[i] = local_fft[i]
                    combined[i + N] = local_fft[i] # placeholder partner

                for i in range(N):
                    angle = -2 * math.pi * step / (num_steps if num_steps > 0 else 1)
                    local_fft[i] = combined[i] + combined[N + i] * complex(math.cos(angle), math.sin(angle))

        return local_fft

def unified_phi_c():
    return 0.93

def check_invariants(phi_c):
    return {
        "ghost": phi_c > GHOST,
        "loopseal": phi_c > LOOPSEAL,
        "gap_sovereign": phi_c < GAP_SOVEREIGN
    }
