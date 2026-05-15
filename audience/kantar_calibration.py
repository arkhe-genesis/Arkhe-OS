#!/usr/bin/env python3
"""
kantar_calibration.py — Calibração do fator de conversão Twitch → TV aberta
Utiliza dados históricos da Kantar Ibope Media para treinar um modelo de regressão
que estima a audiência real da TV a partir dos viewers de plataformas de streaming.
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json, hashlib, time

@dataclass
class CalibrationDataPoint:
    """Um ponto de calibração: medição simultânea Twitch + Kantar."""
    timestamp: float
    broadcaster: str           # emissora (globo, sbt, etc.)
    time_slot: str             # "morning", "afternoon", "prime_time", "late_night"
    genre: str                 # "news", "telenovela", "sports", "entertainment", "general"
    twitch_viewers: int        # viewers no Twitch no momento
    kantar_rating_points: float  # pontos de audiência Kantar Ibope
    kantar_viewers: int        # audiência real estimada (conversão de rating)
    conversion_factor: float   # Fator calculado: kantar_viewers / twitch_viewers

class KantarCalibrationEngine:
    """
    Motor de calibração do fator de conversão Twitch → TV.

    Método:
    1. Coletar dados históricos pareados (Twitch + Kantar) para cada emissora
    2. Treinar modelo de regressão por faixa horária e gênero
    3. Validar contra dados de teste (holdout)
    4. Publicar fatores calibrados para uso em produção
    """

    def __init__(self):
        self.data: List[CalibrationDataPoint] = []
        self.models: Dict[str, LinearRegression] = {}  # (time_slot, genre) → model
        self.factors: Dict[str, float] = {}            # (time_slot, genre) → factor
        self.overall_r2: float = 0.0

    def load_kantar_data(self, data_path: str):
        """Carrega dados históricos da Kantar (formato CSV/JSON)."""
        # Em produção: carregar de banco de dados seguro
        # Formato esperado: CSV com colunas timestamp, broadcaster, time_slot, genre,
        #                   twitch_viewers, kantar_rating_points
        import pandas as pd
        df = pd.read_csv(data_path)

        for _, row in df.iterrows():
            # Converter rating points → viewers estimados
            # 1 rating point = 1% dos domicílios com TV na região
            kantar_viewers = int(row['kantar_rating_points'] * 750000)  # ~75M domicílios no Brasil

            factor = kantar_viewers / max(1, row['twitch_viewers'])

            self.data.append(CalibrationDataPoint(
                timestamp=row['timestamp'],
                broadcaster=row['broadcaster'],
                time_slot=row['time_slot'],
                genre=row['genre'],
                twitch_viewers=int(row['twitch_viewers']),
                kantar_rating_points=float(row['kantar_rating_points']),
                kantar_viewers=kantar_viewers,
                conversion_factor=factor,
            ))

        print(f"✅ {len(self.data)} pontos de calibração carregados")

    def train_models(self):
        """Treina modelos de regressão por faixa horária e gênero."""
        if not self.data:
            print("❌ No data to train models")
            return

        time_slots = set(d.time_slot for d in self.data)
        genres = set(d.genre for d in self.data)

        for slot in time_slots:
            for genre in genres:
                subset = [d for d in self.data if d.time_slot == slot and d.genre == genre]
                if len(subset) < 10:
                    continue  # Dados insuficientes para este segmento

                X = np.array([[d.twitch_viewers] for d in subset])
                y = np.array([d.kantar_viewers for d in subset])

                # Split treino/teste
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Treinar modelo linear
                model = LinearRegression()
                model.fit(X_train, y_train)

                # Avaliar
                y_pred = model.predict(X_test)
                r2 = r2_score(y_test, y_pred)
                mape = mean_absolute_percentage_error(y_test, y_pred)

                key = f"{slot}_{genre}"
                self.models[key] = model
                self.factors[key] = model.coef_[0]  # Coeficiente = fator de conversão

                print(f"   {slot}/{genre}: fator={model.coef_[0]:.1f}, R²={r2:.3f}, MAPE={mape:.2%}")

        # Calcular R² global
        all_X = np.array([[d.twitch_viewers] for d in self.data])
        all_y = np.array([d.kantar_viewers for d in self.data])
        all_pred = np.array([self.predict_tv_viewers(d.twitch_viewers, d.time_slot, d.genre) for d in self.data])

        if len(self.data) >= 2:
            self.overall_r2 = r2_score(all_y, all_pred)
        else:
            self.overall_r2 = 0.0

        print(f"\n✅ Modelos treinados. R² global: {self.overall_r2:.3f}")

    def predict_tv_viewers(self, twitch_viewers: int, time_slot: str, genre: str = "general") -> int:
        """Prediz audiência real da TV a partir de viewers do Twitch."""
        key = f"{time_slot}_{genre}"

        # Usar modelo treinado se disponível
        if key in self.models:
            predicted = self.models[key].predict(np.array([[twitch_viewers]]))[0]
            return max(0, int(predicted))

        # Fallback: usar fator padrão da faixa horária
        default_factors = {
            "prime_time": 120,    # 1 viewer Twitch ≈ 120 telespectadores TV
            "afternoon": 65,      # 1 viewer Twitch ≈ 65 telespectadores TV
            "morning": 40,        # 1 viewer Twitch ≈ 40 telespectadores TV
            "late_night": 25,     # 1 viewer Twitch ≈ 25 telespectadores TV
        }

        factor = default_factors.get(time_slot, 50)
        return int(twitch_viewers * factor)

    def generate_calibration_report(self) -> Dict:
        """Gera relatório de calibração com selo canônico."""
        report = {
            "calibration_timestamp": time.time(),
            "data_points": len(self.data),
            "overall_r2": self.overall_r2,
            "factors": {},
            "models_trained": len(self.models),
        }

        for key, factor in self.factors.items():
            slot, genre = key.split('_', 1)
            report["factors"][f"{slot}/{genre}"] = {
                "factor": round(factor, 2),
                "r2": None,  # Preencher com métrica do modelo específico
            }

        # Selo canônico
        report["canonical_seal"] = hashlib.sha3_256(
            json.dumps(report, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        return report
