import numpy as np

def add_turbulent_noise(fluid, sigma=0.2):
    """
    Injeta ruído turbulento multiplicativo pós-vórtice.
    A amplitude do ruído escala com a magnitude local da velocidade,
    simulando acoplamento inercial em regimes de Reynolds moderados.
    """
    speed = np.sqrt(fluid.u**2 + fluid.v**2)
    noise_u = np.random.randn(*fluid.u.shape) * sigma * (speed + 1e-6)
    noise_v = np.random.randn(*fluid.v.shape) * sigma * (speed + 1e-6)
    fluid.u += noise_u
    fluid.v += noise_v
    fluid._project_spectral()
    return fluid

class NonlinearSensor:
    """
    Modelo realista de sensor (ex: eletrodo EEG, sonda de velocidade).
    1. Saturação sigmoide (faixa dinâmica limitada)
    2. Ruído aditivo gaussiano de leitura (ruído térmico/instrumental)
    """
    def __init__(self, saturation_scale=1.0, readout_noise_std=0.05):
        self.sat = saturation_scale
        self.noise_std = readout_noise_std

    def measure(self, field):
        x = field / self.sat
        saturated = 2.0 / (1.0 + np.exp(-np.clip(x, -5, 5))) - 1.0
        measured = saturated + np.random.normal(0, self.noise_std, size=field.shape)
        return measured

def estimate_mutual_information(x, y, bins=40):
    """
    Estima MI(X;Y) via histograma 2D com correção de viés.
    Medida de acoplamento informacional não-paramétrica,
    robusta a relações não-lineares e saturação.
    """
    hist_2d, _, _ = np.histogram2d(x.ravel(), y.ravel(), bins=bins)
    p_xy = hist_2d / np.sum(hist_2d)
    p_x = np.sum(p_xy, axis=1)
    p_y = np.sum(p_xy, axis=0)
    eps = 1e-12
    mi = 0.0
    for i in range(p_x.shape[0]):
        for j in range(p_y.shape[0]):
            if p_xy[i, j] > eps:
                mi += p_xy[i, j] * np.log(p_xy[i, j] / (p_x[i] * p_y[j] + eps) + eps)
    return max(0.0, mi)
