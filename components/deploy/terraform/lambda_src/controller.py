import json
import os
import boto3
import snowflake.connector
from collections import deque
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class CoherenceState:
    lambda_score: float
    timestamp: datetime
    latency: float
    throughput: float
    error_rate: float

class SBMController:
    def __init__(self):
        self.lambda_target = float(os.environ.get('LAMBDA_TARGET', 0.95))
        self.hysteresis = float(os.environ.get('HYSTERESIS', 0.02))
        self.memory = deque(maxlen=300)  # 5 min de histórico
        self.env = os.environ.get('ENVIRONMENT', 'dev')

        # Clients AWS
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.kinesis = boto3.client('kinesis')

        # Snowflake connection (lazy)
        self._sf_conn = None

    @property
    def sf_conn(self):
        if not self._sf_conn:
            # In production, fetch from Secrets Manager
            self._sf_conn = snowflake.connector.connect(
                account=os.environ.get('SNOWFLAKE_ACCOUNT'),
                user=os.environ.get('SNOWFLAKE_USER'),
                password=os.environ.get('SNOWFLAKE_PASSWORD'),
                warehouse=f"ARKHE_WH_{self.env.upper()}",
                database=f"ARKHE_{self.env.upper()}"
            )
        return self._sf_conn

    def calculate_lambda2(self, metrics: Dict[str, float]) -> float:
        """Calcula λ₂-data baseado nas métricas do pipeline"""
        latency_stability = 1 - min(metrics['latency_p99'] / 60.0, 1)
        throughput_eff = min(metrics['throughput_actual'] / metrics['throughput_expected'], 1)
        reliability = 1 - metrics['error_rate']
        cost_stability = 1 - min(metrics.get('cost_variance', 0) / 100.0, 1)

        return (0.35 * latency_stability +
                0.35 * throughput_eff +
                0.20 * reliability +
                0.10 * cost_stability)

    def predict_coherence(self) -> float:
        """Predição AR(1) simples para λ₂(t+1)"""
        if len(self.memory) < 10:
            return self.memory[-1].lambda_score if self.memory else 0.95
        scores = [s.lambda_score for s in list(self.memory)[-10:]]
        return 2 * scores[-1] - scores[-2]  # Extrapolação linear

    def evaluate_and_act(self):
        # Coleta métricas do Snowflake
        # Mocking for blueprint demo
        metrics = {
            'latency_p99': 5.0,
            'throughput_actual': 950,
            'throughput_expected': 1000,
            'error_rate': 0.01,
            'cost_variance': 5
        }

        lambda_current = self.calculate_lambda2(metrics)
        lambda_predicted = self.predict_coherence()

        state = CoherenceState(
            lambda_score=lambda_current,
            timestamp=datetime.now(timezone.utc),
            latency=metrics['latency_p99'],
            throughput=metrics['throughput_actual'],
            error_rate=metrics['error_rate']
        )
        self.memory.append(state)

        # Lógica de controle com histerese e predição
        action = self._decide_action(lambda_current, lambda_predicted)

        # Publica métricas no CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace='Arkhe/DataPlatform',
                MetricData=[{
                    'MetricName': 'Lambda2DataCoherence',
                    'Value': lambda_current,
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': self.env},
                        {'Name': 'Pipeline', 'Value': 'core'}
                    ]
                }]
            )
        except:
            pass

        return {
            'lambda_current': lambda_current,
            'lambda_predicted': lambda_predicted,
            'action': action,
            'state': asdict(state)
        }

    def _decide_action(self, current: float, predicted: float) -> str:
        """Lógica de decisão com histerese"""
        if current < (self.lambda_target - self.hysteresis - 0.05) or predicted < 0.85:
            return 'CIRCUIT_BREAK'
        elif current > (self.lambda_target + self.hysteresis + 0.02):
            return 'SCALE_DOWN'
        elif current < (self.lambda_target - self.hysteresis):
            return 'SCALE_UP'
        return 'MAINTAIN'

def lambda_handler(event, context):
    controller = SBMController()
    result = controller.evaluate_and_act()
    return {
        'statusCode': 200,
        'body': json.dumps(result, default=str)
    }
