import numpy as np
import time

try:
    from core.omega_transducer import OmegaTransducer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from core.omega_transducer import OmegaTransducer

class PygfxScaffold:
    """Mock Pygfx scaffold for integration testing."""
    def __init__(self, **kwargs):
        self.state = {'kappa': kwargs.get('kappa', 0.75), 'coherence': 0.5}

    def get_state(self):
        return self.state

    def compute_coherence(self):
        return self.state['coherence']

    def step(self, adjustment):
        self.state['kappa'] += adjustment.get('kappa_delta', 0.0)
        self.state['kappa'] = np.clip(self.state['kappa'], 0.1, 2.0)

        # Simulate coherence change based on adjustment
        if adjustment['reason'] == 'scalar_intent_high':
            self.state['coherence'] += 0.05
        elif adjustment['reason'] == 'scalar_intent_low':
            self.state['coherence'] -= 0.05

        self.state['coherence'] = np.clip(self.state['coherence'], 0.0, 1.0)
        return self.state

class OmegaEnabledScaffold:
    """Scaffold with integrated Omega transducer for scalar-longitudinal perception."""

    def __init__(self, transducer_config: dict, scaffold_params: dict):
        self.transducer = OmegaTransducer(**transducer_config)
        # Integration with Pygfx scaffold mock
        self.scaffold = PygfxScaffold(**scaffold_params)
        self.perception_history = []

    def perceive_and_adjust(self, sensor_input: np.ndarray) -> dict:
        """Perceive via Omega transducer and adjust scaffold coherence."""
        # Transduce: vector -> scalar
        scalar_intent = self.transducer.vector_to_scalar(sensor_input)

        # Evaluate scaffold state
        current_state = self.scaffold.get_state()
        coherence = self.scaffold.compute_coherence()

        # Decision: adjust kappa based on scalar intent and current coherence
        if scalar_intent > 0.9 and coherence < 0.85:
            # High intent, low coherence: increase coupling
            adjustment = {'kappa_delta': +0.05, 'reason': 'scalar_intent_high'}
        elif scalar_intent < 0.3 and coherence > 0.95:
            # Low intent, high coherence: reduce coupling to avoid overfitting
            adjustment = {'kappa_delta': -0.03, 'reason': 'scalar_intent_low'}
        else:
            # Maintain current trajectory
            adjustment = {'kappa_delta': 0.0, 'reason': 'balanced'}

        # Apply adjustment via SPSA + Gluing
        updated_state = self.scaffold.step(adjustment)

        # Generate feedback signal
        feedback_scalar = updated_state['coherence']
        feedback_tem = self.transducer.scalar_to_vector(feedback_scalar)

        # Record perception loop
        self.perception_history.append({
            'timestamp': time.time(),
            'scalar_intent': scalar_intent,
            'coherence': coherence,
            'adjustment': adjustment,
            'feedback_magnitude': float(np.linalg.norm(feedback_tem))
        })

        return {
            'scalar_intent': scalar_intent,
            'coherence': coherence,
            'adjustment': adjustment,
            'feedback': feedback_tem,
            'loop_closed': True
        }
