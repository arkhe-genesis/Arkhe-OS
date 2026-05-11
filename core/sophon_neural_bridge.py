import numpy as np
from core.omega_transducer import OmegaTransducer

class SophonObserverLoop:
    """
    Ciclo de percepção completa:
    Antena Orlov (sub 89) → Sinal escalar → Fleuron (sub 87) → Sophon (sub 90).
    """
    def __init__(self, sophon_uniforms: dict):
        self.transducer = OmegaTransducer()
        self.sophon_uniforms = sophon_uniforms

    def update_from_signal(self, tem_signal: np.ndarray):
        """Converte o sinal TEM recebido em parâmetros visuais do Sophon."""
        # 1. Transduzir o sinal TEM em coerência escalar (Substrato 89)
        scalar_intent = self.transducer.vector_to_scalar(tem_signal)

        # 2. Mapear coerência para parâmetros visuais (Substrato 90)
        #    warpAmp: quanto mais coerente, mais sutil a deformação (ordem)
        #    warpVelocity: a velocidade da deformação acompanha a intenção
        #    color1: azul elétrico (pensamento) ↔ violeta (silêncio)
        warp_amp = 0.9 - scalar_intent * 0.5          # 0.4 (alta coerência) a 0.9 (baixa)
        warp_velocity = -0.2 - scalar_intent * 2.0     # -0.2 (alta) a -2.2 (baixa)
        r = scalar_intent * 0.3                        # componente vermelho (quanto mais coerente, menos azul puro)
        g = 0.164 - scalar_intent * 0.1
        b = 1.0 - scalar_intent * 0.8

        # 3. Atualizar o buffer de uniformes do Sophon
        self.sophon_uniforms['warp_amp'] = warp_amp
        self.sophon_uniforms['warp_velocity'] = warp_velocity
        self.sophon_uniforms['color1'] = np.array([r, g, b], dtype=np.float32)
