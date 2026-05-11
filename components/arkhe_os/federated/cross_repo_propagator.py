import logging
from collections import defaultdict, deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrossRepoPropagator")

class CrossRepoPropagator:
    """
    Handles propagation of coherence gradients across repository dependencies.
    """
    def __init__(self):
        self.dependency_graph = defaultdict(list)
        self.propagation_history = []

    def add_dependency(self, source_repo, target_repo, dep_type="general"):
        self.dependency_graph[source_repo].append({"target": target_repo, "type": dep_type})

    def validate_graph(self):
        """
        Detects cycles and ghost dependencies in the graph before propagation.
        """
        visited = set()
        rec_stack = set()

        def is_cyclic(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor_info in self.dependency_graph.get(node, []):
                neighbor = neighbor_info["target"]
                if neighbor not in visited:
                    if is_cyclic(neighbor):
                        return True
                elif neighbor in rec_stack:
                    logger.warning(f"Cycle detected involving {node} and {neighbor}")
                    return True
            rec_stack.remove(node)
            return False

        for node in list(self.dependency_graph.keys()):
            if node not in visited:
                if is_cyclic(node):
                    return False

        logger.info("Graph validation passed: No cycles detected.")
        return True

    def calculate_adaptive_weight(self, dep_type):
        """
        Assigns adaptive weights. Critical dependencies (like security)
        have more influence on coherence propagation.
        """
        weights = {
            "security": 1.5,
            "core": 1.2,
            "general": 1.0,
            "ui": 0.8,
            "experimental": 0.5
        }
        return weights.get(dep_type, 1.0)

    def calculate_semantic_distance(self, domain_a, domain_b):
        """
        Limits propagation by semantic distance to prevent nonsensical coherence flow
        (e.g., from ML straight to crypto).
        Returns distance 0-1 (0 = same, 1 = max difference).
        """
        # simplified mock distances
        distances = {
            ("ml", "crypto"): 0.9,
            ("crypto", "ml"): 0.9,
            ("ml", "data"): 0.2,
            ("crypto", "security"): 0.1,
            ("core", "security"): 0.3
        }
        return distances.get((domain_a, domain_b), 0.5)

    def propagate_coherence(self, initial_coherence_map):
        """
        Propagates coherence scores based on validated graph, adaptive weights,
        and semantic distance limits.
        """
        if not self.validate_graph():
            logger.error("Propagation aborted due to graph validation failure.")
            return initial_coherence_map

        updated_coherence = dict(initial_coherence_map)

        # Simple BFS propagation
        queue = deque(initial_coherence_map.keys())
        processed = set()

        while queue:
            current = queue.popleft()
            if current in processed:
                continue
            processed.add(current)

            current_coherence = updated_coherence.get(current, {"score": 0, "domain": "general"})

            for neighbor_info in self.dependency_graph.get(current, []):
                target = neighbor_info["target"]
                dep_type = neighbor_info["type"]

                target_coherence = updated_coherence.get(target, {"score": 0, "domain": "general"})

                weight = self.calculate_adaptive_weight(dep_type)
                semantic_dist = self.calculate_semantic_distance(current_coherence["domain"], target_coherence["domain"])

                # Limit propagation if semantic distance is too high (e.g. > 0.8)
                if semantic_dist > 0.8:
                    logger.info(f"Propagation limited from {current} to {target} due to high semantic distance ({semantic_dist}).")
                    continue

                # Attenuate propagation over distance
                propagation_factor = weight * (1.0 - semantic_dist) * 0.1
                propagated_score = current_coherence["score"] * propagation_factor

                target_coherence["score"] = min(1.0, target_coherence["score"] + propagated_score)
                updated_coherence[target] = target_coherence

                self.propagation_history.append({
                    "source": current,
                    "target": target,
                    "propagated_amount": propagated_score,
                    "weight_applied": weight,
                    "semantic_distance": semantic_dist
                })

                if target not in processed:
                    queue.append(target)

        return updated_coherence

    def get_audit_trail(self):
        """
        Registrar histórico de propagação para debugging e auditoria forense.
        """
        return self.propagation_history
