# simulate_lambda2_validation.py
import random
import math
from datetime import datetime, timezone, timedelta

class ArkheSimulator:
    def __init__(self, scenario='stable', duration_minutes=60):
        self.scenario = scenario
        self.duration = duration_minutes
        self.timestamps = []
        self.metrics = {
            'latency_p99': [],
            'throughput_actual': [],
            'throughput_expected': [],
            'error_rate': [],
            'cost_variance': []
        }
        self.lambda2_history = []
        self.actions = []

    def generate_metrics(self):
        random.seed(42)
        base_time = datetime.now()
        for i in range(self.duration):
            current_time = base_time + timedelta(minutes=i)
            self.timestamps.append(current_time)
            if self.scenario == 'stable':
                lat = random.gauss(2.0, 0.5)
                thr = random.gauss(950, 50)
                err = random.uniform(0.005, 0.015)
                cost = random.gauss(5, 2)
            elif self.scenario == 'degrading':
                if i < 30:
                    lat = random.gauss(2.0, 0.5)
                    thr = 950
                    err = 0.01
                    cost = 5
                else:
                    progress = (i - 30) / 30
                    lat = 2.0 + (20 * progress) + random.uniform(-2, 2)
                    thr = 950 * (1 - progress * 0.4)
                    err = 0.01 + (0.15 * progress)
                    cost = 5 + (20 * progress)
            else:  # chaotic
                lat = random.expovariate(1/5.0) + random.choice([0, 15])
                thr = random.gauss(800, 200)
                err = 0.05
                cost = random.expovariate(1/30.0)

            self.metrics['latency_p99'].append(max(0.1, lat))
            self.metrics['throughput_actual'].append(max(100, thr))
            self.metrics['throughput_expected'].append(1000)
            self.metrics['error_rate'].append(max(0, min(1, err)))
            self.metrics['cost_variance'].append(max(0, cost))

    def calculate_lambda2(self, idx):
        lat = self.metrics['latency_p99'][idx]
        thr = self.metrics['throughput_actual'][idx]
        thr_exp = self.metrics['throughput_expected'][idx]
        err = self.metrics['error_rate'][idx]
        cost = self.metrics['cost_variance'][idx]
        latency_stability = 1 - min(lat / 60.0, 1)
        throughput_eff = min(thr / thr_exp, 1)
        reliability = 1 - err
        cost_stability = 1 - min(cost / 100.0, 1)
        lambda2 = (0.35 * latency_stability + 0.35 * throughput_eff + 0.20 * reliability + 0.10 * cost_stability)
        return max(0, min(1, lambda2))

    def simulate(self):
        lambda_target = 0.95
        hysteresis = 0.02
        for i in range(self.duration):
            lam = self.calculate_lambda2(i)
            self.lambda2_history.append(lam)
            if lam < (lambda_target - hysteresis - 0.05):
                action = 'CIRCUIT_BREAK'
            elif lam > (lambda_target + hysteresis + 0.02):
                action = 'SCALE_DOWN'
            else:
                action = 'MAINTAIN'
            self.actions.append(action)

if __name__ == "__main__":
    for scenario in ['stable', 'degrading', 'chaotic']:
        sim = ArkheSimulator(scenario=scenario)
        sim.generate_metrics()
        sim.simulate()
        mean_lam = sum(sim.lambda2_history) / len(sim.lambda2_history)
        breaches = sum(1 for x in sim.lambda2_history if x < 0.90)
        print("Scenario: %-10s | Mean lambda2: %.3f | Breaches: %d" % (scenario, mean_lam, breaches))
