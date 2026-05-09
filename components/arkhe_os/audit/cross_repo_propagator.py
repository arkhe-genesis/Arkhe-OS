import networkx as nx
import numpy as np
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class RepoCoherenceState:
    """State of a repository in the cross-repo coherence graph."""
    repo_id: str
    local_coherence: float  # Φ_C computed from local audit
    dependency_weights: Dict[str, float]  # repo_id → weight
    semantic_domain: str  # e.g., "security", "ml", "web", "infra"
    last_updated: float
    propagation_history: List[Dict] = field(default_factory=list)

class CrossRepoCoherencePropagator:
    """Propagate coherence metrics across dependency graph — Substrato 259."""

    def __init__(
        self,
        dependency_graph: nx.DiGraph,
        alpha: float = 0.85,  # Inertia factor
        beta: float = 0.5,    # Semantic distance decay
        max_iterations: int = 50,
        convergence_threshold: float = 1e-4,
    ):
        self.graph = dependency_graph
        self.alpha = alpha
        self.beta = beta
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.repo_states: Dict[str, RepoCoherenceState] = {}
        self.propagation_log: List[Dict] = []

    def register_repo(self, repo_id: str, local_coherence: float,
                     semantic_domain: str, dependencies: Dict[str, float]):
        """Register a repository with its local audit results."""
        self.repo_states[repo_id] = RepoCoherenceState(
            repo_id=repo_id,
            local_coherence=local_coherence,
            dependency_weights=dependencies,
            semantic_domain=semantic_domain,
            last_updated=datetime.now().timestamp()
        )
        # Ensure graph has node
        if repo_id not in self.graph:
            self.graph.add_node(repo_id, domain=semantic_domain)
        # Add dependency edges
        for dep_id, weight in dependencies.items():
            if dep_id not in self.graph:
                self.graph.add_node(dep_id)
            self.graph.add_edge(repo_id, dep_id, weight=weight)

    def _semantic_distance(self, domain_a: str, domain_b: str) -> float:
        """Compute semantic distance between two domains."""
        # Simplified: predefined distance matrix
        domain_hierarchy = {
            'security': {'security': 0, 'crypto': 0.2, 'infra': 0.5, 'ml': 0.8, 'web': 0.7},
            'crypto': {'security': 0.2, 'crypto': 0, 'infra': 0.4, 'ml': 0.9, 'web': 0.6},
            'infra': {'security': 0.5, 'crypto': 0.4, 'infra': 0, 'ml': 0.6, 'web': 0.5},
            'ml': {'security': 0.8, 'crypto': 0.9, 'infra': 0.6, 'ml': 0, 'web': 0.4},
            'web': {'security': 0.7, 'crypto': 0.6, 'infra': 0.5, 'ml': 0.4, 'web': 0},
        }
        return domain_hierarchy.get(domain_a, {}).get(domain_b, 1.0)

    def propagate_once(self) -> Dict[str, float]:
        """Single iteration of coherence propagation."""
        new_values = {}
        for repo_id, state in self.repo_states.items():
            # Start with local coherence (inertia)
            propagated = self.alpha * state.local_coherence

            # Add influence from dependencies
            influence_sum = 0.0
            weight_sum = 0.0
            for neighbor in self.graph.predecessors(repo_id):
                if neighbor in self.repo_states:
                    neighbor_state = self.repo_states[neighbor]
                    edge_weight = self.graph[neighbor][repo_id].get('weight', 1.0)
                    semantic_decay = np.exp(-self.beta * self._semantic_distance(
                        neighbor_state.semantic_domain, state.semantic_domain
                    ))
                    influence = edge_weight * semantic_decay * neighbor_state.local_coherence
                    influence_sum += influence
                    weight_sum += edge_weight * semantic_decay

            if weight_sum > 0:
                propagated += (1 - self.alpha) * (influence_sum / weight_sum)

            new_values[repo_id] = np.clip(propagated, 0.0, 1.0)

        return new_values

    def run_propagation(self) -> Dict[str, Dict]:
        """Run full propagation until convergence or max iterations."""
        for iteration in range(self.max_iterations):
            old_values = {rid: state.local_coherence for rid, state in self.repo_states.items()}
            new_values = self.propagate_once()

            # Check convergence
            max_change = max(
                (abs(new_values[rid] - old_values[rid]) for rid in new_values if rid in old_values),
                default=0.0
            )

            # Update states
            for repo_id, new_val in new_values.items():
                if repo_id in self.repo_states:
                    old_val = self.repo_states[repo_id].local_coherence
                    self.repo_states[repo_id].propagation_history.append({
                        'iteration': iteration,
                        'old_value': old_val,
                        'new_value': new_val,
                        'change': abs(new_val - old_val)
                    })
                    self.repo_states[repo_id].local_coherence = new_val
                    self.repo_states[repo_id].last_updated = datetime.now().timestamp()

            if max_change < self.convergence_threshold:
                self.propagation_log.append({
                    'converged': True,
                    'iterations': iteration + 1,
                    'final_max_change': max_change
                })
                break
        else:
            self.propagation_log.append({
                'converged': False,
                'iterations': self.max_iterations
            })

        return {
            repo_id: {
                'local_coherence': state.local_coherence,
                'propagated_coherence': state.local_coherence,  # After propagation
                'semantic_domain': state.semantic_domain,
                'dependency_count': len(state.dependency_weights),
                'propagation_steps': len(state.propagation_history)
            }
            for repo_id, state in self.repo_states.items()
        }

    def identify_coherence_anomalies(self, threshold: float = 0.15) -> List[Dict]:
        """Find repos where propagated coherence differs significantly from local."""
        anomalies = []
        for repo_id, state in self.repo_states.items():
            # Compare initial local vs. final propagated
            if state.propagation_history:
                initial = state.propagation_history[0]['old_value']
                final = state.local_coherence
                if abs(final - initial) > threshold:
                    anomalies.append({
                        'repo_id': repo_id,
                        'local_coherence': initial,
                        'propagated_coherence': final,
                        'delta': final - initial,
                        'semantic_domain': state.semantic_domain,
                        'likely_cause': 'dependency_influence' if final < initial else 'positive_dependency_effect'
                    })
        return anomalies

    def get_propagation_stats(self) -> Dict:
        return {
            'total_repos': len(self.repo_states),
            'graph_edges': self.graph.number_of_edges(),
            'convergence_log': self.propagation_log[-1] if self.propagation_log else None,
            'avg_coherence': float(np.mean([s.local_coherence for s in self.repo_states.values()])) if self.repo_states else 0.0,
            'coherence_std': float(np.std([s.local_coherence for s in self.repo_states.values()])) if self.repo_states else 0.0,
            'anomalies_detected': len(self.identify_coherence_anomalies())
        }
