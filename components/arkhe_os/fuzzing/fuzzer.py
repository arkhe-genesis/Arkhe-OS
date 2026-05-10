import math
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CoherentFuzzer")

class CoherentFuzzer:
    """
    Balance exploration (low coherence) and exploitation (crash discovery)
    via a utility function. Uses AST-aware mutations for structured languages.
    """
    def __init__(self, initial_corpus=None, novelty_threshold=0.01):
        self.corpus = initial_corpus or []
        self.novelty_threshold = novelty_threshold
        self.total_mutations = 0
        self.novelty_discovered = 0
        self.mutation_weights = {"insert": 0.3, "delete": 0.2, "modify": 0.5}

    def utility_function(self, coverage_gain, crash_probability):
        """
        Balances exploration and exploitation.
        Returns a score combining coverage (exploration) and crash likelihood (exploitation).
        """
        # Phi optimization
        phi = 1.618033988749895
        return (coverage_gain * phi) + (crash_probability / phi)

    def ast_mutate(self, lfir_node):
        """
        Simulates AST-aware mutations based on LFIR types from polymath.go.
        Avoids generating syntactically invalid inputs.
        """
        # LFIRNodeType concepts from polymath.go: LFIRModule, LFIRFunction, LFIRType, etc.
        valid_types = ["LFIRModule", "LFIRFunction", "LFIRType", "LFIRVariable", "LFIROperation", "LFIRControlFlow", "LFIRQuantumLink", "LFIRMetadata"]

        if lfir_node.get("type") not in valid_types:
            logger.warning(f"Unknown LFIR type: {lfir_node.get('type')}. Treating cautiously.")

        action = random.choices(
            list(self.mutation_weights.keys()),
            weights=list(self.mutation_weights.values())
        )[0]

        mutated_node = dict(lfir_node)

        if action == "modify":
            mutated_node["mutated"] = True
            mutated_node["id"] = mutated_node.get("id", "") + "_m"
        elif action == "insert":
            # simulate adding a child node logically
            mutated_node["children_count"] = mutated_node.get("children_count", 0) + 1
        elif action == "delete":
            if mutated_node.get("children_count", 0) > 0:
                mutated_node["children_count"] -= 1

        return mutated_node

    def maintain_corpus(self, input_data, coherence_score):
        """
        Maintains a diverse corpus. Does not discard "medium coherence" inputs
        as they may lead to new paths.
        """
        # Accept inputs that are not just "perfect" coherence
        if coherence_score > 0.2: # arbitrary threshold for "medium" coherence
            self.corpus.append(input_data)
            self.novelty_discovered += 1
            return True
        return False

    def should_stop(self):
        """
        Implements early stopping based on diminishing returns (novelty rate < threshold).
        """
        if self.total_mutations < 100:
            return False # allow burn-in period

        novelty_rate = self.novelty_discovered / self.total_mutations
        if novelty_rate < self.novelty_threshold:
            logger.info(f"Early stopping triggered. Novelty rate {novelty_rate:.4f} < {self.novelty_threshold}")
            return True
        return False

    def self_optimize(self, findings):
        """
        Permitir que o fuzzer reflita sobre sua própria estratégia e proponha auto-otimizações via consenso interno.
        """
        logger.info("Fuzzer internal consensus triggered for self-optimization.")

        success_insert = sum(1 for f in findings if f.get("action") == "insert" and f.get("success"))
        success_modify = sum(1 for f in findings if f.get("action") == "modify" and f.get("success"))
        success_delete = sum(1 for f in findings if f.get("action") == "delete" and f.get("success"))

        total = max(1, success_insert + success_modify + success_delete)

        # Softmax-like adjustment with internal consensus
        self.mutation_weights["insert"] = (self.mutation_weights["insert"] + (success_insert / total)) / 2
        self.mutation_weights["modify"] = (self.mutation_weights["modify"] + (success_modify / total)) / 2
        self.mutation_weights["delete"] = (self.mutation_weights["delete"] + (success_delete / total)) / 2

        logger.info(f"New mutation weights post consensus: {self.mutation_weights}")
        return self.mutation_weights

    def run_fuzzing_step(self, seed_node):
        self.total_mutations += 1
        mutated = self.ast_mutate(seed_node)

        # simulate evaluation
        cov = random.random()
        crash = random.random() * 0.1
        util = self.utility_function(cov, crash)

        coherence = random.random()
        self.maintain_corpus(mutated, coherence)

        return mutated, util
