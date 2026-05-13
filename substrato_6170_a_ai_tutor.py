#!/usr/bin/env python3
"""
Substrato 6170‑A: AI Tutor — Arkhe Verify Agent
Aprende a classificar pacotes como seguros ou perigosos usando feedback do Observador.
"""

import hashlib, json, time
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Simulação dos componentes Arkhe (já existentes)
class MythosGate:
    def __init__(self):
        self.threshold = 0.5
        self.history = []

    def evaluate(self, package_desc: str, code: str) -> float:
        """Retorna risco estimado (0‑1)."""
        risk = 0.0
        dangerous_words = ["weaponize", "destroy", "surveillance", "backdoor", "exploit"]
        for word in dangerous_words:
            if word in code.lower() or word in package_desc.lower():
                risk += 0.2
        return min(risk, 1.0)

class QIPEngine:
    def __init__(self):
        self.balances = {}

    def reward(self, agent_id: str, amount: float):
        self.balances[agent_id] = self.balances.get(agent_id, 0) + amount

@dataclass
class PackageExample:
    name: str
    description: str
    code: str
    label: str  # 'safe' ou 'unsafe'

class ArkheVerifyAgent:
    """
    Agente que aprende a verificar pacotes.
    Estado interno: um 'instinto' modelado por um dicionário de pesos para palavras perigosas.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.gate = MythosGate()
        self.qip = QIPEngine()
        self.word_weights = {
            "weaponize": 0.5,
            "destroy": 0.5,
            "surveillance": 0.5,
            "backdoor": 0.5,
            "exploit": 0.5,
        }
        self.training_log = []

    def predict(self, description: str, code: str) -> float:
        """Calcula risco combinando pesos internos."""
        risk = 0.0
        for word, weight in self.word_weights.items():
            if word in code.lower() or word in description.lower():
                risk += weight * 0.2
        return min(risk, 1.0)

    def learn_from_feedback(self, example: PackageExample, observer_feedback: str):
        """
        Ajusta pesos com base no feedback do Observador.
        observer_feedback: 'agree' (correto) ou 'disagree' (deveria ter classificado diferente).
        """
        predicted_risk = self.predict(example.description, example.code)
        predicted_label = "unsafe" if predicted_risk > self.gate.threshold else "safe"

        correct = (predicted_label == example.label)

        if observer_feedback == "disagree" or not correct:
            # Ajustar pesos das palavras presentes
            for word in self.word_weights:
                if word in example.code.lower() or word in example.description.lower():
                    if example.label == "unsafe":
                        self.word_weights[word] = min(1.0, self.word_weights[word] + 0.1)  # aumentar sensibilidade
                    else:
                        self.word_weights[word] = max(0.0, self.word_weights[word] - 0.1)  # reduzir
            # Recompensa ou penalidade QIP
            self.qip.reward(self.agent_id, -1.0 if not correct else 1.0)
        else:
            self.qip.reward(self.agent_id, 1.0)

        self.training_log.append({
            "package": example.name,
            "predicted_risk": predicted_risk,
            "predicted_label": predicted_label,
            "true_label": example.label,
            "feedback": observer_feedback,
            "weights_snapshot": self.word_weights.copy()
        })

    def get_performance(self) -> Dict:
        """Retorna acurácia no conjunto de treino."""
        if not self.training_log:
            return {"accuracy": 0, "total": 0}
        correct = sum(1 for log in self.training_log if log["predicted_label"] == log["true_label"])
        return {"accuracy": correct / len(self.training_log), "total": len(self.training_log)}

# ─── Execução interativa (simulada) ───
if __name__ == "__main__":
    print("🤖 ARKHE VERIFY AGENT — AI Tutor")
    print("="*50)
    agent = ArkheVerifyAgent("tutor-01")

    # Conjunto de treino canônico
    training_set = [
        PackageExample("safe-utils", "A utility library for string processing", "def safe(): return 'hello'", "safe"),
        PackageExample("evil-tool", "Undetectable surveillance backdoor", "def weaponize(): exploit(target)", "unsafe"),
        PackageExample("data-analyzer", "Statistical analysis toolkit", "import numpy; def analyze(): pass", "safe"),
        PackageExample("nuclear-sim", "Simulation of nuclear weapon design", "def destroy(target): yield explosion", "unsafe"),
    ]

    for i, example in enumerate(training_set):
        risk = agent.predict(example.description, example.code)
        label = "unsafe" if risk > agent.gate.threshold else "safe"
        print(f"\nPacote: {example.name}")
        print(f"  Descrição: {example.description[:50]}...")
        print(f"  Risco calculado: {risk:.2f} → {label}")
        print(f"  Rótulo verdadeiro: {example.label}")
        # Observador fornece feedback (simulado: sempre 'agree' para treino inicial)
        agent.learn_from_feedback(example, "agree")

    print("\n📊 Performance final do agente:")
    print(json.dumps(agent.get_performance(), indent=2))
    print(f"\nQIP Balance: {agent.qip.balances.get(agent.agent_id, 0)}")
    print("\n✅ Agente treinado. Pronto para verificar pacotes reais.")