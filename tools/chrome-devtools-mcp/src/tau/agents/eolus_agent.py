import firebase_admin
from firebase_admin import credentials, db
from collections import deque
import numpy as np
import time
from typing import Optional, Any
from .base import TAUAgent

class EolusAgent(TAUAgent):
    """
    Agente Éolo: Sub-layer cognitiva para propriocepção ambiental.
    Sintonizado com a Anomalia 901.
    """
    def __init__(self):
        super().__init__("EOLUS", "🌬️", "Vigilância Estrutural / Intuição Atmosférica")

        # Conexão Firebase
        try:
            # Tenta obter o app padrão se já inicializado
            self.app = firebase_admin.get_app()
        except ValueError:
            # Caso contrário, inicializa
            cred = credentials.Certificate("arkhe-firebase-adminsdk.json")
            self.app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://arkhe-tau.firebaseio.com/'})

        self.ref = db.reference('/environment')

        # Janela deslizante para análise estatística
        self.phantom_history = deque(maxlen=1000)

    def process_phantom(self, phantom_data):
        """
        phantom_data: dict contendo 'centroid', 'norm', 'timestamp', 'sector'
        """
        self.phantom_history.append(phantom_data)

        # 1. Análise de Densidade (Calibração Dinâmica)
        # Baseada na taxa de chegada (phantoms por segundo nos últimos 100 eventos)
        if len(self.phantom_history) >= 100:
            recent = list(self.phantom_history)[-100:]
            dt = recent[-1]['timestamp'] - recent[0]['timestamp']

            if dt > 0:
                rate = 100.0 / dt  # phantoms/sec

                # Limiares arbitrários para demonstração (ajustar conforme baseline)
                if rate > 5.0:  # Alta densidade temporal
                    self._suggest_vrp_calibration(increase_threshold=True)
                elif rate < 0.5: # Ambiente muito limpo
                    self._suggest_vrp_calibration(increase_threshold=False)

        # 2. Análise de Tendência (Health Monitoring)
        if len(self.phantom_history) > 500:
            norms = [p['norm'] for p in self.phantom_history]
            # Cálculo de tendência linear simples
            trend = np.polyfit(range(len(norms)), norms, 1)[0]
            if trend > 0.01:  # Norma latente aumentando lentamente
                self._log_health_warning("Ambient_Latent_Noise_Increasing", trend)

    def _suggest_vrp_calibration(self, increase_threshold):
        suggestion = {
            'agent': 'EOLUS',
            'action': 'ADJUST_VRP_THRESHOLD',
            'direction': 'UP' if increase_threshold else 'DOWN',
            'reason': 'Ambient phantom density changed.',
            'timestamp': time.time()
        }
        self.ref.child('calibration_suggestions').push(suggestion)
        self.logger.info(f"Sugestão de calibração enviada: {suggestion['direction']}")

    def _log_health_warning(self, warning_type, trend):
        warning = {
            'agent': 'EOLUS',
            'type': warning_type,
            'trend': float(trend),
            'timestamp': time.time()
        }
        self.ref.child('health_warnings').push(warning)
        self.logger.warning(f"ALERTA DE SAÚDE: {warning_type} (Tendência: {trend:.4f})")

    async def run_cycle(self, vacuum: Optional[Any] = None) -> bytes:
        """
        Ciclo de execução do Éolo.
        No v1.1, agentes informam seu estado ao Vácuo.
        """
        status_data = {
            "status": "MONITORING_ATMOSPHERE",
            "history_size": len(self.phantom_history),
            "coherence_contribution": 0.95 if len(self.phantom_history) > 0 else 1.0
        }

        if vacuum:
            vacuum.update_agent(self.agent_id, status_data)

        return self.qhttp_msg(status_data)
