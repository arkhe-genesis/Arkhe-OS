import asyncio, time, subprocess, pickle, json, os
from pathlib import Path
from field_transfer_learning import FieldTransferLearner, LoRaCalibrationPolicy, FieldDataset
from torch.utils.data import DataLoader

class ContinuousFineTuner:
    def __init__(self, data_dir: str, policy_path: str, ota_endpoint: str,
                 gap_threshold=8.0, cooldown_minutes=30):
        self.data_dir = Path(data_dir)
        self.policy_path = policy_path
        self.ota_endpoint = ota_endpoint
        self.gap_threshold = gap_threshold
        self.cooldown = cooldown_minutes * 60
        self.last_train_time = 0

    async def monitor_and_retrain(self):
        while True:
            # Carrega os dados mais recentes
            csv_path = self.data_dir / "field_data.csv"
            if not csv_path.exists():
                await asyncio.sleep(60)
                continue
            import pandas as pd
            df = pd.read_csv(csv_path)
            recent = df[df['timestamp'] > time.time() - 3600]  # última hora
            if recent.empty:
                await asyncio.sleep(30)
                continue

            avg_gap = recent['gap'].mean()
            print(f"Gap médio (última hora): {avg_gap:.2f}")

            if avg_gap > self.gap_threshold and (time.time() - self.last_train_time) > self.cooldown:
                print("⚠️ Degradação detectada. Iniciando fine‑tuning...")
                # Construir episódios a partir do CSV
                episodes = self._build_episodes(recent)
                if episodes:
                    learner = FieldTransferLearner(
                        LoRaCalibrationPolicy(6,3),
                        sim_policy_path=self.policy_path,
                        alpha=0.01, meta_lr=1e-4, domain_reg_lambda=0.1
                    )
                    ds = FieldDataset(episodes)
                    loader = DataLoader(ds, batch_size=4, shuffle=True)
                    await asyncio.to_thread(learner.meta_step, loader, 30)
                    # Salva nova política
                    new_policy_path = self.data_dir / "field_policy_latest.pt"
                    learner.save_field_policy(str(new_policy_path))
                    # Envia OTA (simulação via scp)
                    subprocess.run(["scp", str(new_policy_path), self.ota_endpoint])
                    self.last_train_time = time.time()
                    print("✅ Política atualizada e enviada OTA.")
            await asyncio.sleep(120)  # verifica a cada 2 min

    def _build_episodes(self, df):
        episodes = []
        for node_id, group in df.groupby('node_id'):
            # agrupa em janelas de 30 pontos consecutivos
            for start in range(0, len(group)-30, 15):
                chunk = group.iloc[start:start+30]
                observations = chunk[['gap','sf','rssi']].values  # simplificado
                actions = chunk[['sf']].values - 7  # ajuste
                rewards = -chunk['gap'].values * 0.1
                gaps = chunk['gap'].values
                episodes.append(FieldEpisode(observations, actions, rewards, gaps, {}))
        return episodes

if __name__ == "__main__":
    asyncio.run(ContinuousFineTuner("/data/field", "sim_policy.pt", "user@gateway:/ota/").monitor_and_retrain())
