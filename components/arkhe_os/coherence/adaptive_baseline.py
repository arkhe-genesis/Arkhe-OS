import yaml
from typing import Dict

class AdaptiveBaseline:
    """Gerencia baseline EMA por destino com configuração YAML."""

    def __init__(self, config_path: str = "config/ping_baseline.yaml"):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)['ping_baseline']
        self.alpha = config['alpha']
        self.r_max = config['r_max_ms']
        self.baselines: Dict[str, float] = {
            t: cfg['initial_baseline_ms']
            for t, cfg in config.get('targets', {}).items()
        }
        self.default_initial = config['default_initial_ms']

    def update(self, target: str, rtt: float) -> float:
        """Atualiza baseline EMA e retorna o valor suavizado."""
        current = self.baselines.get(target, self.default_initial)
        new_baseline = self.alpha * rtt + (1 - self.alpha) * current
        self.baselines[target] = new_baseline
        return new_baseline

    def get_baseline(self, target: str) -> float:
        """Retorna baseline atual para o destino sem atualizar."""
        return self.baselines.get(target, self.default_initial)
