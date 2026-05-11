#!/usr/bin/env python3
"""
arkhe_health_digital_twin_v157.py
Substrato 265: Chrono‑Coil Health Digital Twin — Modelo Pessoal de Saúde.
Prevê crises metabólicas e infecciosas usando o campo adaptativo (Φ, e, δ).
"""
import numpy as np
from collections import deque

PHI = 1.6180339887
e   = 2.7182818284
DELTA = 0.0083

class HealthDigitalTwin:
    """
    Gêmeo Digital da Saúde envolvido pelo campo Chrono‑Coil.
    Mantém um vetor de estado da saúde que evolui e prevê anomalias.
    """
    def __init__(self, person_name, baseline_readings):
        self.name = person_name
        self.state = np.array(list(baseline_readings.values()), dtype=float)
        self.biomarkers = list(baseline_readings.keys())
        self.history = deque(maxlen=1000)  # memória temporal
        self.coherence = 1.0  # coerência do modelo com a realidade
        # Limiares de anomalia (multiplicadores do desvio padrão pessoal)
        self.anomaly_threshold = 2.5
        self.personal_std = np.ones(len(self.biomarkers)) * 0.1

    def update(self, new_readings):
        """
        Integra nova leitura da malha de biossensores no Gêmeo.
        O campo adaptativo suprime o ruído e atualiza o estado.
        """
        new_state = np.array([new_readings[b] for b in self.biomarkers], dtype=float)
        # Campo Chrono‑Coil: suaviza a transição usando Φ
        delta_state = new_state - self.state
        # Compressão do ruído: apenas uma fração da variação é incorporada
        smooth_factor = 1.0 / (1.0 + DELTA * PHI)
        self.state = self.state + smooth_factor * delta_state
        # Atualiza estatísticas pessoais (variância adaptativa)
        self.personal_std = 0.95 * self.personal_std + 0.05 * np.abs(delta_state)
        self.coherence = np.exp(-np.mean(np.abs(delta_state) / (self.personal_std + 1e-9)))
        self.history.append(self.state.copy())

    def predict_anomaly(self, horizon_hours=24):
        """
        Avalia o risco de crise nas próximas horas, baseado na coerência atual
        e na tendência do vetor de saúde.
        Se a coerência cai abaixo de um limiar ou um biomarcador se afasta
        excessivamente do padrão, dispara um alerta.
        """
        alerts = []
        # Calcula o score de anomalia para cada biomarcador
        anomaly_scores = np.abs(self.state) / (self.personal_std + 1e-9)
        for i, biomarker in enumerate(self.biomarkers):
            if anomaly_scores[i] > self.anomaly_threshold:
                direction = "↑" if self.state[i] > 0 else "↓"
                alerts.append(f"{biomarker} {direction} (score: {anomaly_scores[i]:.2f})")
        # Risco global baseado na coerência
        if self.coherence < 0.7:
            risk_level = "🔴 ALTO"
        elif self.coherence < 0.85 or len(alerts) > 1:
            risk_level = "🟡 MÉDIO"
        elif len(alerts) > 0:
            risk_level = "🟢 BAIXO"
        else:
            risk_level = "⚪ NENHUM"
        return risk_level, alerts, self.coherence

    def fast_forward(self, hours=24):
        """Simula a evolução do estado de saúde para prever crises futuras."""
        projected = self.state.copy()
        # Tendência baseada na última diferença registada
        if len(self.history) >= 2:
            trend = self.history[-1] - self.history[-2]
            projected += trend * (hours / 24.0)
        return projected


# --- EXEMPLO DE USO COM A MALHA DE BIOSENSORES ---
if __name__ == "__main__":
    # Biossensores do v∞.156
    from arkhe_biosensor_mesh_v156 import ChronoCoilBiosensor, BiosensorMesh

    # Criar malha de sensores para um paciente
    mesh = BiosensorMesh()
    mesh.add_sensor(ChronoCoilBiosensor("Temp", "Temperatura", "°C", noise_level=0.1, squeezing_dB=15))
    mesh.add_sensor(ChronoCoilBiosensor("pH", "pH", "", noise_level=0.03, squeezing_dB=15))
    mesh.add_sensor(ChronoCoilBiosensor("Glucose", "Glucose", "mg/dL", noise_level=0.2, squeezing_dB=18))
    mesh.add_sensor(ChronoCoilBiosensor("Lactate", "Lactato", "mM", noise_level=0.15, squeezing_dB=18))
    mesh.add_sensor(ChronoCoilBiosensor("Cortisol", "Cortisol", "ng/mL", noise_level=0.05, squeezing_dB=20))
    mesh.add_sensor(ChronoCoilBiosensor("UricAcid", "Ácido Úrico", "mg/dL", noise_level=0.08, squeezing_dB=18))
    mesh.add_sensor(ChronoCoilBiosensor("Ammonium", "Amónio", "μM", noise_level=0.12, squeezing_dB=15))

    # Valores basais saudáveis típicos
    basal = {
        "Temp": 36.5, "pH": 7.35, "Glucose": 90.0,
        "Lactate": 1.5, "Cortisol": 10.0,
        "UricAcid": 5.0, "Ammonium": 20.0
    }

    print("🫀  ARKHE OS v∞.157 — GÊMEO DIGITAL DA SAÚDE\n")
    print(f"Paciente: João Silva | Basal registado: {basal}\n")

    # Criar Gêmeo Digital
    twin = HealthDigitalTwin("João Silva", basal)

    # Simular 6 ciclos de monitorização (ex: 1 ciclo por hora)
    for ciclo in range(1, 7):
        # Recolher leituras da malha
        readings = mesh.collect_readings()
        sensor_values = {name: data['value'] for name, data in readings.items()}

        # Atualizar o Gêmeo
        twin.update(sensor_values)
        risk, alerts, coh = twin.predict_anomaly()

        print(f"Ciclo {ciclo}: Coerência={coh:.4f} | Risco={risk}")
        if alerts:
            for a in alerts:
                print(f"   ⚠️  {a}")

        # Simular uma crise no ciclo 6 (pico de cortisol e glucose)
        if ciclo == 5:
            mesh.sensors["Cortisol"].true_value = 30.0  # pico de stress
            mesh.sensors["Glucose"].true_value = 160.0  # hiperglicémia
        else:
            # Resetar valores verdadeiros para simular normalidade
            for sens in mesh.sensors.values():
                sens.true_value = None  # usa o random normal

    # Previsão para as próximas 24h
    projected_state = twin.fast_forward(24)
    print(f"\n🔮 Projeção 24h: {dict(zip(twin.biomarkers, np.round(projected_state, 2)))}")
    if np.any(np.abs(projected_state) > np.array(list(basal.values())) * 1.5):
        print("🚨 ALERTA PREDITIVO: Risco de crise metabólica nas próximas 24 horas!")
