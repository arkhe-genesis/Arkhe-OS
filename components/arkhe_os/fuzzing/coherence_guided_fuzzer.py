import numpy as np
import random
from datetime import datetime
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

class MutationStrategy(Enum):
    STRUCTURAL = "structural"      # AST-level changes (add/remove nodes)
    SEMANTIC = "semantic"          # Type-preserving value changes
    ADVERSARIAL = "adversarial"    # Boundary/extreme values
    CROSS_DOMAIN = "cross_domain"  # Inject patterns from other domains

@dataclass
class FuzzInput:
    """Input candidate for coherence-guided fuzzing."""
    input_id: str
    raw_data: bytes
    coherence_estimate: float
    mutation_history: List[Dict] = field(default_factory=list)
    execution_result: Optional[Dict] = None
    novelty_score: float = 0.0

    def compute_hash(self) -> str:
        return hashlib.sha256(self.raw_data).hexdigest()[:16]

@dataclass
class CoherenceModel:
    """Bayesian model for predicting Φ_C given input features."""
    # Simplified: in production, use GP or neural net
    feature_weights: Dict[str, float]
    baseline_coherence: float
    uncertainty: float = 0.1

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Return (predicted_Φ_C, uncertainty)"""
        score = self.baseline_coherence
        for feat, weight in self.feature_weights.items():
            score += weight * features.get(feat, 0)
        score = np.clip(score, 0.0, 1.0)
        return score, self.uncertainty

class CoherenceGuidedFuzzer:
    """Fuzzer that uses coherence estimates to guide input generation."""

    def __init__(
        self,
        module_under_test: Callable,
        coherence_estimator: Callable,
        initial_seeds: List[bytes],
        config: Dict,
    ):
        self.module = module_under_test
        self.estimate_coherence = coherence_estimator
        self.config = config
        self.corpus: Dict[str, FuzzInput] = {}
        self.high_value_corpus: List[FuzzInput] = []
        self.coherence_model = self._init_coherence_model(initial_seeds)
        self.mutation_strategies = self._init_mutation_strategies()
        self.stats = {
            'inputs_generated': 0,
            'crashes_found': 0,
            'coherence_drops': 0,
            'novel_paths': 0,
        }

    def _init_coherence_model(self, seeds: List[bytes]) -> CoherenceModel:
        """Initialize model with baseline from seed inputs."""
        scores = [self.estimate_coherence(s) for s in seeds]
        return CoherenceModel(
            feature_weights={
                'input_size': -0.02,      # Larger inputs → slightly lower Φ_C
                'entropy': -0.05,          # High entropy → more unpredictable
                'structural_complexity': -0.03,
            },
            baseline_coherence=float(np.mean(scores)) if scores else 0.5,
            uncertainty=float(np.std(scores)) + 0.1 if scores else 0.1
        )

    def _init_mutation_strategies(self) -> Dict[MutationStrategy, Callable]:
        return {
            MutationStrategy.STRUCTURAL: self._mutate_structural,
            MutationStrategy.SEMANTIC: self._mutate_semantic,
            MutationStrategy.ADVERSARIAL: self._mutate_adversarial,
            MutationStrategy.CROSS_DOMAIN: self._mutate_cross_domain,
        }

    def _compute_utility(self, input_candidate: FuzzInput) -> float:
        """Compute utility U(x) for selection."""
        # Term 1: Low coherence is desirable for exploration
        coherence_term = self.config.get('lambda1', 0.4) * (1 - input_candidate.coherence_estimate)

        # Term 2: Crash discovery (if already executed)
        crash_term = 0.0
        if input_candidate.execution_result:
            if input_candidate.execution_result.get('crashed'):
                crash_term = self.config.get('lambda2', 0.5)

        # Term 3: Novelty based on coverage distance
        novelty_term = self.config.get('lambda3', 0.1) * input_candidate.novelty_score

        return coherence_term + crash_term + novelty_term

    def select_parent_input(self) -> Optional[FuzzInput]:
        """Select input for mutation using utility-based sampling."""
        if not self.corpus:
            return None
        # Softmax over utilities
        utilities = np.array([self._compute_utility(inp) for inp in self.corpus.values()])
        if np.max(utilities) <= 0:
            # Fallback to random
            return random.choice(list(self.corpus.values()))
        probs = np.exp(utilities - np.max(utilities))
        probs /= np.sum(probs)
        selected = np.random.choice(list(self.corpus.values()), p=probs)
        return selected

    def mutate(self, parent: FuzzInput, strategy: MutationStrategy) -> FuzzInput:
        """Apply mutation strategy to generate new input."""
        mutator = self.mutation_strategies[strategy]
        new_data, mutation_info = mutator(parent.raw_data)

        new_input = FuzzInput(
            input_id=f"{parent.input_id}_mut_{len(parent.mutation_history)+1}",
            raw_data=new_data,
            coherence_estimate=self.estimate_coherence(new_data),
            mutation_history=parent.mutation_history + [mutation_info],
            novelty_score=self._compute_novelty(new_data)
        )
        return new_input

    def _mutate_structural(self, data: bytes) -> Tuple[bytes, Dict]:
        """AST-aware structural mutation (placeholder)."""
        # In production: parse to AST, apply transformations
        # Example: duplicate a node, remove optional field, reorder siblings
        mutation_info = {'type': 'structural', 'operation': 'node_duplicate'}
        # Simplified: add random byte sequence at random position
        pos = random.randint(0, len(data))
        injection = bytes([random.randint(0, 255) for _ in range(random.randint(1, 10))])
        return data[:pos] + injection + data[pos:], mutation_info

    def _mutate_semantic(self, data: bytes) -> Tuple[bytes, Dict]:
        """Type-preserving semantic mutation."""
        # Example: flip bits in numeric fields, change string casing
        mutation_info = {'type': 'semantic', 'operation': 'bit_flip'}
        if not data:
            return data, mutation_info
        # Flip a random byte
        pos = random.randint(0, len(data) - 1)
        data_list = bytearray(data)
        data_list[pos] ^= 0xFF  # Bitwise NOT
        return bytes(data_list), mutation_info

    def _mutate_adversarial(self, data: bytes) -> Tuple[bytes, Dict]:
        """Boundary/extreme value mutation."""
        mutation_info = {'type': 'adversarial', 'operation': 'extreme_value'}
        # Inject max/min values, very long strings, etc.
        extremes = [b'\x00' * 100, b'\xFF' * 100, b'<' * 1000, b'-' * 10000]
        injection = random.choice(extremes)
        pos = random.randint(0, len(data))
        return data[:pos] + injection + data[pos:], mutation_info

    def _mutate_cross_domain(self, data: bytes) -> Tuple[bytes, Dict]:
        """Inject patterns from other domains (e.g., SQL in JSON)."""
        mutation_info = {'type': 'cross_domain', 'operation': 'pattern_injection'}
        # Example: inject SQL-like patterns into a JSON input
        sql_patterns = [b"'; DROP TABLE users; --", b"1' OR '1'='1", b"UNION SELECT"]
        injection = random.choice(sql_patterns)
        pos = random.randint(0, len(data))
        return data[:pos] + injection + data[pos:], mutation_info

    def _compute_novelty(self, new_data: bytes) -> float:
        """Compute novelty score based on distance from existing corpus."""
        if not self.corpus:
            return 1.0
        # Simplified: hash-based distance
        new_hash = hashlib.sha256(new_data).digest()
        min_dist = min(
            np.sum(np.frombuffer(new_hash, dtype=np.uint8) != np.frombuffer(hashlib.sha256(inp.raw_data).digest(), dtype=np.uint8))
            for inp in self.corpus.values()
        )
        return float(min_dist) / len(new_hash)  # Normalize to [0,1]

    def execute_and_observe(self, input_candidate: FuzzInput) -> Dict:
        """Execute module with input and collect observations."""
        try:
            start_time = datetime.now().timestamp()
            result = self.module(input_candidate.raw_data)
            end_time = datetime.now().timestamp()

            # Re-estimate coherence post-execution (dynamic analysis)
            try:
                post_coherence = self.estimate_coherence(input_candidate.raw_data, dynamic=True)
            except TypeError:
                post_coherence = self.estimate_coherence(input_candidate.raw_data)

            return {
                'success': True,
                'output': result,
                'execution_time_ms': (end_time - start_time) * 1000,
                'coherence_pre': input_candidate.coherence_estimate,
                'coherence_post': post_coherence,
                'coherence_delta': post_coherence - input_candidate.coherence_estimate,
                'crashed': False,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'crashed': True,
                'coherence_pre': input_candidate.coherence_estimate,
            }

    def run_iteration(self) -> Optional[FuzzInput]:
        """Single fuzzing iteration: select → mutate → execute → update."""
        parent = self.select_parent_input()
        if not parent:
            return None

        # Select mutation strategy based on utility of each
        strategy = random.choices(
            list(MutationStrategy),
            weights=[0.3, 0.3, 0.3, 0.1],  # Structural, Semantic, Adversarial, Cross-domain
            k=1
        )[0]

        candidate = self.mutate(parent, strategy)
        self.stats['inputs_generated'] += 1

        # Execute and observe
        observation = self.execute_and_observe(candidate)
        candidate.execution_result = observation

        # Update corpus
        self.corpus[candidate.input_id] = candidate

        # Check for high-value findings
        is_high_value = (
            observation.get('crashed') or
            (observation.get('coherence_delta', 0) < -self.config.get('coherence_drop_threshold', 0.1)) or
            (candidate.novelty_score > self.config.get('novelty_threshold', 0.5))
        )

        if is_high_value:
            self.high_value_corpus.append(candidate)
            if observation.get('crashed'):
                self.stats['crashes_found'] += 1
            elif observation.get('coherence_delta', 0) < 0:
                self.stats['coherence_drops'] += 1
            if candidate.novelty_score > self.config.get('novelty_threshold', 0.5):
                self.stats['novel_paths'] += 1

        # Update coherence model with new observation (online learning)
        self._update_coherence_model(candidate, observation)

        return candidate if is_high_value else None

    def _update_coherence_model(self, input_candidate: FuzzInput, observation: Dict):
        """Simple online update of coherence prediction model."""
        # In production: use Bayesian update or gradient step
        if observation.get('crashed'):
            # Crashes indicate very low coherence → adjust model
            self.coherence_model.baseline_coherence *= 0.99
            self.coherence_model.uncertainty = min(1.0, self.coherence_model.uncertainty + 0.01)

    def get_fuzzing_stats(self) -> Dict:
        return {
            **self.stats,
            'corpus_size': len(self.corpus),
            'high_value_findings': len(self.high_value_corpus),
            'avg_coherence': float(np.mean([inp.coherence_estimate for inp in self.corpus.values()])) if self.corpus else 0.0,
            'model_uncertainty': self.coherence_model.uncertainty,
        }
