with open("ml/zero_day_production_trainer.py", "r") as f:
    content = f.read()

target_block1 = """        # Mock: em produção, consultar banco de dados de telemetria
        n_samples = days_back * 10  # Reduced for tests

        data = []
        for i in range(n_samples):
            # Gerar features sintéticas para demonstração
            sample = {
                feat: np.random.normal(0.5, 0.2) if "percent" in feat or "ratio" in feat
                      else np.random.exponential(1.0) if "count" in feat or "ops" in feat
                      else np.random.uniform(0, 1)
                for feat in self.BEHAVIORAL_FEATURES
            }

            # Label: 1 = zero-day confirmado, 0 = comportamento normal
            # Em produção: usar labels de incidentes confirmados
            is_zero_day = np.random.random() < 0.2  # Increased zero-days ratio"""

new_block1 = """        # Mock: em produção, consultar banco de dados de telemetria
        n_samples = days_back * 1000  # ~1000 amostras/dia

        data = []
        for i in range(n_samples):
            # Gerar features sintéticas para demonstração
            sample = {
                feat: np.random.normal(0.5, 0.2) if "percent" in feat or "ratio" in feat
                      else np.random.exponential(1.0) if "count" in feat or "ops" in feat
                      else np.random.uniform(0, 1)
                for feat in self.BEHAVIORAL_FEATURES
            }

            # Label: 1 = zero-day confirmado, 0 = comportamento normal
            # Em produção: usar labels de incidentes confirmados
            is_zero_day = np.random.random() < 0.02  # 2% de zero-days no dataset """


if target_block1 in content:
    content = content.replace(target_block1, new_block1)

with open("ml/zero_day_production_trainer.py", "w") as f:
    f.write(content)
print("Patched ml successfully")
