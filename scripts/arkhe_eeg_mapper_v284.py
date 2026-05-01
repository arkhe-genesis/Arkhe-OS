import numpy as np
import time
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

def simple_welch(data, fs, nperseg):
    """Uma implementação muito simples e manual do welch sem scipy,
    já que a memória recomenda remover scipy devido a problemas de C-extensions.
    """
    # Just a simple periodogram via FFT for demonstration
    # In real world, use proper windowing and overlapping
    n = len(data)
    if n == 0:
        return np.array([]), np.array([])
    # Apply Hanning window
    window = np.hanning(n)
    data_win = data * window
    # Compute FFT
    fft_vals = np.fft.rfft(data_win)
    # Compute PSD
    psd = np.abs(fft_vals) ** 2 / (fs * n)
    # Compute frequencies
    freqs = np.fft.rfftfreq(n, d=1.0/fs)
    return freqs, psd

class EEGCoherenceMapper:
    """Mapeia bandas EEG para parâmetros de coerência ARKHE."""

    def __init__(self, board_id=BoardIds.SYNTHETIC_BOARD.value):
        # Using SYNTHETIC_BOARD for local testing
        self.params = BrainFlowInputParams()
        self.board_id = board_id
        self.board = BoardShim(board_id, self.params)
        self.sampling_rate = BoardShim.get_sampling_rate(board_id)
        self.window_size = 256  # ~1s a 250Hz
        self.kappa_map = {
            'delta': 0.5,    # Sleep deep
            'theta': 1.0,    # Relaxation
            'alpha': 2.5,    # Focus intense
            'beta': 5.0,     # Flow creativity
            'gamma': 10.0,   # Meditation deep
            'high_gamma': 25.0  # Love unconditional / Arkhe architect
        }

    def start_acquisition(self):
        self.board.prepare_session()
        self.board.start_stream()

    def get_coherence_params(self, channel=0) -> dict:
        """Extrai κ e C_brain de dados EEG em tempo real."""
        # Obter dados da janela deslizante
        data = self.board.get_current_board_data(self.window_size)
        if data.shape[1] < self.window_size:
            # Not enough data yet
            return {
                'kappa': 1.0,
                'c_brain': 0.3,
                'band_powers': {},
                'timestamp': time.time()
            }

        # Select a channel
        eeg_channels = BoardShim.get_eeg_channels(self.board_id)
        eeg = data[eeg_channels[channel]]

        # Calcular potência por banda (substituindo scipy.signal.welch)
        freqs, psd = simple_welch(eeg, fs=self.sampling_rate, nperseg=128)

        bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100),
            'high_gamma': (100, 150)
        }

        # Potência relativa por banda
        total_power = np.sum(psd)
        if total_power == 0:
            total_power = 1e-9 # avoid division by zero

        band_powers = {}
        for name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs <= high)
            band_powers[name] = float(np.sum(psd[mask]) / total_power)

        # Calcular κ ponderado por potência das bandas
        kappa = sum(band_powers[band] * k for band, k in self.kappa_map.items())

        # C_brain: normalizar kappa para [0.3, 1.0]
        c_brain = 0.3 + 0.7 * min(1.0, kappa / 25.0)  # Saturar em κ=25

        return {
            'kappa': float(kappa),
            'c_brain': float(c_brain),
            'band_powers': band_powers,
            'timestamp': time.time()
        }

    def stop_acquisition(self):
        self.board.stop_stream()
        self.board.release_session()

if __name__ == "__main__":
    mapper = EEGCoherenceMapper()
    mapper.start_acquisition()
    try:
        print("Aguardando dados...")
        time.sleep(2) # wait for buffer to fill
        for _ in range(5):
            params = mapper.get_coherence_params()
            print(f"κ: {params['kappa']:.2f}, C_brain: {params['c_brain']:.2f}")
            time.sleep(0.5)
    finally:
        mapper.stop_acquisition()
        print("Teste EEG real-time simulado completo.")
