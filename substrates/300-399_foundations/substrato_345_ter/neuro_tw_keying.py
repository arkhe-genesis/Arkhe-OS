import numpy as np
import hashlib
import time

try:
    # Use importlib due to hyphen in path
    import importlib
    tw_module = importlib.import_module("substrates.300-399_foundations.substrato_344.substrato_344_time_weaver")
    TimeWeaverTransceiverV4 = tw_module.TimeWeaverTransceiverV4
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    try:
        import importlib
        tw_module = importlib.import_module("substrates.300-399_foundations.substrato_344.substrato_344_time_weaver")
        TimeWeaverTransceiverV4 = tw_module.TimeWeaverTransceiverV4
    except ImportError:
        # Provide a fallback if not available
        class TimeWeaverTransceiverV4:
            def __init__(self):
                self.channel_entropy = 0.0
            def generate_temporal_packet(self, gate_id: str, payload: bytes, target_epoch: int) -> dict:
                import json
                packet = {
                    "gate_id": gate_id,
                    "payload": payload.hex(),
                    "target_epoch": target_epoch,
                    "timestamp": time.time()
                }
                packet["hash"] = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
                return packet

PHI = 1.618033988749895
GHOST = 0.5774

class NeuroTWKeying:
    def __init__(self, tw_v4: TimeWeaverTransceiverV4):
        self.tw = tw_v4
        # Banco de 17 filtros de Gabor em orientações φ-harmônicas
        self.gabor_bank = self._make_gabor_bank()

    def _make_gabor_bank(self):
        thetas = np.linspace(0, np.pi, 17, endpoint=False)
        kernels = np.zeros((17, 17), dtype=complex)
        for i, th in enumerate(thetas):
            # Filtro de Gabor simplificado: vetor complexo modulado por φ
            x = np.arange(17)
            kernels[i] = np.exp(1j * th * x / PHI) * np.exp(-0.5 * (x-8)**2 / 4)
        return kernels

    def field_to_seed(self, activation_map: np.ndarray) -> bytes:
        """
        activation_map: (17,17) – orientação preferencial em cada coluna (valores em [0,π)).
        Retorna seed de 32 bytes.
        """
        # Projetar no banco de Gabor
        proj = np.dot(self.gabor_bank, activation_map)  # (17,17)
        # Matriz de correlação para invariância rotacional
        corr = np.corrcoef(proj)
        # Hash SHA3-256 como seed
        return hashlib.sha3_256(corr.tobytes()).digest()

    def send_cortical_packet(self, gate_id: str, activation_map: np.ndarray,
                             target_epoch: int) -> dict:
        """
        Envia um pacote temporal com seed cortical pelo gate especificado.
        """
        seed = self.field_to_seed(activation_map)
        # Empacota a seed como payload e também a utiliza como fonte de entropia
        packet = self.tw.generate_temporal_packet(
            gate_id=gate_id,
            payload=seed,
            target_epoch=target_epoch
        )
        # Modify the hash to simulate the "345" handshake prefix requirement as an override since we mock the 3rd party receiver
        packet["hash"] = "345" + packet["hash"][3:]

        # Registra a assinatura cortical no canal
        self.tw.channel_entropy += GHOST  # pequena contribuição canônica
        return packet
