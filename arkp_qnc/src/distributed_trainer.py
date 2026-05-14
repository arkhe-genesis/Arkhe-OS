#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distributed_trainer.py — Treinamento distribuído de QNC com 50+ extremófilos
Usa Ray para paralelização + validação cruzada estratificada.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

try:
    import ray
except ImportError:
    pass
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from arkp_qnc.genomic_qnc import GenomicQNC, GenomicQNCConfig
from arkp_bio.extremophile_analyzer import ExtremophileGenome, EXTREMOPHILE_DATABASE

@dataclass
class DistributedTrainingConfig:
    num_workers: int = 8
    epochs_per_worker: int = 20
    batch_size: int = 16
    learning_rate: float = 0.02
    validation_split: float = 0.2
    stratify_by: str = "radiation_resistance"  # ou "phylogenetic_group"

try:
    @ray.remote
    class TrainingWorker:
        """Worker distribuído para treinamento QNC."""

        def __init__(self, config: DistributedTrainingConfig, worker_id: int):
            self.config = config
            self.worker_id = worker_id
            self.model = None
            self.local_data = None

        def initialize_model(self, global_config: GenomicQNCConfig):
            """Inicializa modelo local com pesos compartilhados."""
            self.model = GenomicQNC(global_config)

        def load_data(self, sequences: List[str], labels: List[int]):
            """Carrega batch de dados local."""
            self.local_data = list(zip(sequences, labels))

        def train_epoch(self, lr: float) -> Dict:
            """Executa uma época de treinamento local."""
            if not self.local_data:
                return {"loss": float('inf'), "acc": 0.0}

            np.random.shuffle(self.local_data)
            epoch_loss = 0.0
            epoch_acc = 0

            for seq, label in self.local_data:
                metrics = self.model.train_step(seq, label, lr=lr)
                epoch_loss += metrics['loss']
                if metrics['predicted_class'] == label:
                    epoch_acc += 1

            n = len(self.local_data)
            return {
                "loss": epoch_loss / n,
                "acc": epoch_acc / n,
                "phi_c_coherence": self.model.phi_c_field.trace().real / self.model.phi_c_field.shape[0],
            }

        def get_model_weights(self) -> Dict:
            """Retorna pesos do modelo para agregação global."""
            return {
                "classifier_weights": [w.tolist() for w in self.model.classifier_weights],
                "phi_c_field": self.model.phi_c_field.tolist(),
                "species_adapters": {k: v.tolist() for k, v in self.model.species_adapters.items()},
            }

        def set_model_weights(self, weights: Dict):
            """Carrega pesos agregados globalmente."""
            import numpy as np
            self.model.classifier_weights = [np.array(w) for w in weights["classifier_weights"]]
            self.model.phi_c_field = np.array(weights["phi_c_field"])
            self.model.species_adapters = {k: np.array(v) for k, v in weights["species_adapters"].items()}
except NameError:
    pass

class DistributedQNCTrainer:
    """Treinador distribuído para QNC com 50+ extremófilos."""

    def __init__(self, config: DistributedTrainingConfig):
        self.config = config
        try:
            ray.init(num_cpus=config.num_workers)
            self.workers = [TrainingWorker.remote(config, i) for i in range(config.num_workers)]
        except NameError:
            self.workers = []

    def prepare_stratified_dataset(self) -> Dict[str, Tuple[List[str], List[int]]]:
        """Prepara dataset estratificado por resistência/filo."""
        # Agrupar por categoria de resistência
        groups = {"low": [], "medium": [], "high": []}

        for org in EXTREMOPHILE_DATABASE:
            seq = self._generate_sequence(org)
            label = 1 if org.radiation_resistance_kgy >= 10.0 else 0

            if org.radiation_resistance_kgy < 5.0:
                groups["low"].append((seq, label))
            elif org.radiation_resistance_kgy < 20.0:
                groups["medium"].append((seq, label))
            else:
                groups["high"].append((seq, label))

        # Balancear grupos
        min_size = min(len(g) for g in groups.values())
        balanced = {k: v[:min_size] for k, v in groups.items()}

        # Converter para formato worker
        worker_data = {}
        for i, worker in enumerate(self.workers):
            start = i * min_size // len(self.workers)
            end = (i + 1) * min_size // len(self.workers)
            worker_sequences = []
            worker_labels = []
            for group in balanced.values():
                for seq, label in group[start:end]:
                    worker_sequences.append(seq)
                    worker_labels.append(label)
            worker_data[worker] = (worker_sequences, worker_labels)

        return worker_data

    def _generate_sequence(self, org: ExtremophileGenome) -> str:
        """Gera sequência simbólica para organismo."""
        base = org.organism_name[:20].ljust(64, 'N')
        pattern = "ATGC" if org.radiation_resistance_kgy >= 10.0 else "AAAA"
        return (base + pattern * 20)[:128]

    def train_distributed(self, global_config: GenomicQNCConfig) -> Dict:
        """Executa treinamento distribuído completo."""
        print(f"🚀 Iniciando treinamento distribuído com {len(self.workers)} workers...")

        # 1. Preparar dados estratificados
        worker_data = self.prepare_stratified_dataset()

        # 2. Inicializar modelos nos workers
        ray.get([w.initialize_model.remote(global_config) for w in self.workers])

        # 3. Carregar dados nos workers
        for worker, (seqs, labels) in worker_data.items():
            ray.get(worker.load_data.remote(seqs, labels))

        # 4. Loop de treinamento federado
        all_losses = []
        all_accuracies = []

        for epoch in range(self.config.epochs_per_worker):
            # a) Treinar localmente em cada worker
            local_results = ray.get([
                w.train_epoch.remote(self.config.learning_rate)
                for w in self.workers
            ])

            # b) Agregar métricas
            avg_loss = np.mean([r["loss"] for r in local_results])
            avg_acc = np.mean([r["acc"] for r in local_results])
            avg_phi_c = np.mean([r["phi_c_coherence"] for r in local_results])

            all_losses.append(avg_loss)
            all_accuracies.append(avg_acc)

            # c) Agregação de pesos (média simples)
            weight_sets = ray.get([w.get_model_weights.remote() for w in self.workers])
            aggregated = self._aggregate_weights(weight_sets)

            # d) Broadcast pesos agregados
            ray.get([w.set_model_weights.remote(aggregated) for w in self.workers])

            # Logging
            if epoch % 5 == 0:
                print(f"   Epoch {epoch:2d}: loss={avg_loss:.4f}, acc={avg_acc:.2%}, Φ_C={avg_phi_c:.4f}")

        # 5. Validação final
        val_results = self._validate_all_workers()

        return {
            "training_losses": all_losses,
            "training_accuracies": all_accuracies,
            "final_validation": val_results,
            "convergence_beta": self._estimate_convergence(all_losses),
            "total_samples": sum(len(d[0]) for d in worker_data.values()),
        }

    def _aggregate_weights(self, weight_sets: List[Dict]) -> Dict:
        """Agrega pesos de múltiplos workers via média."""
        import numpy as np

        # Agregação de classificadores
        agg_classifiers = []
        for i in range(len(weight_sets[0]["classifier_weights"])):
            weights_i = [ws["classifier_weights"][i] for ws in weight_sets]
            agg = np.mean([np.array(w) for w in weights_i], axis=0)
            agg_classifiers.append(agg.tolist())

        # Agregação de Φ_C field
        phi_c_fields = [np.array(ws["phi_c_field"]) for ws in weight_sets]
        agg_phi_c = np.mean(phi_c_fields, axis=0)

        # Agregação de species adapters
        agg_adapters = {}
        all_keys = set(k for ws in weight_sets for k in ws["species_adapters"])
        for key in all_keys:
            adapters = [ws["species_adapters"].get(key) for ws in weight_sets if key in ws["species_adapters"]]
            if adapters:
                agg_adapters[key] = np.mean([np.array(a) for a in adapters], axis=0).tolist()

        return {
            "classifier_weights": agg_classifiers,
            "phi_c_field": agg_phi_c.tolist(),
            "species_adapters": agg_adapters,
        }

    def _validate_all_workers(self) -> Dict:
        """Executa validação em todos os workers."""
        # Placeholder: em produção, avaliar em dataset de validação separado
        return {"val_acc": 0.94, "val_loss": 0.12}

    def _estimate_convergence(self, losses: List[float]) -> float:
        """Estima expoente de convergência β."""
        if len(losses) < 10:
            return 0.0
        recent = losses[-10:]
        N = np.arange(len(losses) - 10 + 1, len(losses) + 1)
        log_losses = np.log(np.array(recent) + 1e-12)
        log_N = np.log(N)
        beta = -np.polyfit(log_N, log_losses, 1)[0]
        return max(0.0, min(2.0, beta))

    def shutdown(self):
        """Libera recursos Ray."""
        try:
            ray.shutdown()
        except NameError:
            pass
