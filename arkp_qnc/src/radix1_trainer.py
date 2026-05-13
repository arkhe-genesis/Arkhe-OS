#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radix1_trainer.py — Substrato 6176: Treinamento QNC em Dados de Extremófilos
Treina a rede quântica para predizer resistência a radiação a partir de genomas.
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .genomic_qnc import GenomicQNC, GenomicQNCConfig
from arkp_bio.extremophile_analyzer import ExtremophileGenome, EXTREMOPHILE_DATABASE

@dataclass
class TrainingConfig:
    epochs: int = 50
    batch_size: int = 4
    learning_rate: float = 0.05
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    phi_c_coupling: float = 0.1

class RADIX1Trainer:
    """Treina GenomicQNC usando dataset de extremófilos."""

    def __init__(self, config: TrainingConfig):
        self.config = config

        # Configurar modelo QNC
        qnc_config = GenomicQNCConfig(
            vocab_size=4,  # A, T, G, C
            max_sequence_length=128,
            embedding_dim=8,
            hidden_dim=16,
            num_classes=2,  # resistant (>=10 kGy) vs sensitive
            num_attention_heads=2,
            phi_c_coupling=config.phi_c_coupling,
            learning_rate=config.learning_rate,
        )
        self.model = GenomicQNC(qnc_config)

        # Métricas
        self.training_metrics: List[Dict] = []
        self.validation_metrics: List[Dict] = []

    def prepare_dataset(self) -> Tuple[List[str], List[int]]:
        """Prepara dataset de treinamento a partir de extremófilos."""
        sequences = []
        labels = []

        for org in EXTREMOPHILE_DATABASE:
            # Gerar sequência simbólica baseada no nome do organismo
            # Em produção: usar sequências reais do NCBI
            seq = self._generate_symbolic_sequence(org.organism_name, org.genome_size_mb)
            sequences.append(seq)

            # Label: 1 = resistente (>= 10 kGy), 0 = sensível
            label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
            labels.append(label)

        return sequences, labels

    def _generate_symbolic_sequence(self, name: str, genome_size_mb: float) -> str:
        """Gera sequência simbólica para treinamento (placeholder)."""
        # Heurística: comprimento proporcional ao tamanho do genoma
        length = min(128, int(genome_size_mb * 30))

        # Padrões baseados no nome (para aprendizado de padrões)
        patterns = {
            'deinococcus': 'ATGC' * 10 + 'GGCC' * 5,
            'thermococcus': 'ATAT' * 8 + 'GCGC' * 7,
            'halobacterium': 'AAAA' * 6 + 'TTTT' * 6 + 'GGGG' * 4,
            'rubrobacter': 'ATGCATGC' * 8,
            'escherichia': 'AT' * 20 + 'GC' * 15,
        }

        base_pattern = 'ATGC'
        for key, pattern in patterns.items():
            if key in name.lower():
                base_pattern = pattern
                break

        # Gerar sequência com padrão + ruído
        sequence = (base_pattern * (length // len(base_pattern) + 1))[:length]

        # Adicionar ruído controlado baseado na resistência
        noise_rate = 0.05 if 'coli' in name.lower() else 0.01
        sequence_list = list(sequence)
        for i in range(len(sequence_list)):
            if np.random.random() < noise_rate:
                sequence_list[i] = np.random.choice(['A', 'T', 'G', 'C'])

        return ''.join(sequence_list)

    def train(self) -> Dict:
        """Executa treinamento completo."""
        print("🧬 Preparando dataset de extremófilos...")
        sequences, labels = self.prepare_dataset()

        # Split train/validation
        split_idx = int(len(sequences) * (1 - self.config.validation_split))
        train_seqs, train_labels = sequences[:split_idx], labels[:split_idx]
        val_seqs, val_labels = sequences[split_idx:], labels[split_idx:]

        print(f"📊 Dataset: {len(train_seqs)} treino, {len(val_seqs)} validação")

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(self.config.epochs):
            # Training epoch
            epoch_loss = 0.0
            epoch_acc = 0

            for seq, label in zip(train_seqs, train_labels):
                metrics = self.model.train_step(seq, label, lr=self.config.learning_rate)
                epoch_loss += metrics['loss']
                if metrics['predicted_class'] == label:
                    epoch_acc += 1

            avg_train_loss = epoch_loss / len(train_seqs) if train_seqs else 0
            avg_train_acc = epoch_acc / len(train_seqs) if train_seqs else 0

            # Validation
            val_loss = 0.0
            val_acc = 0
            for seq, label in zip(val_seqs, val_labels):
                pred_class, confidence = self.model.predict(seq)
                loss = -np.log(confidence if pred_class == label else 1 - confidence + 1e-12)
                val_loss += loss
                if pred_class == label:
                    val_acc += 1

            avg_val_loss = val_loss / len(val_seqs) if val_seqs else 0
            avg_val_acc = val_acc / len(val_seqs) if val_seqs else 0

            # Registrar métricas
            epoch_metrics = {
                'epoch': epoch,
                'train_loss': avg_train_loss,
                'train_acc': avg_train_acc,
                'val_loss': avg_val_loss,
                'val_acc': avg_val_acc,
                'phi_c_coherence': self.model.phi_c_field.trace().real / self.model.phi_c_field.shape[0],
            }
            self.training_metrics.append(epoch_metrics)

            # Logging
            if epoch % 10 == 0:
                print(f"Epoch {epoch:3d}: "
                      f"train_loss={avg_train_loss:.4f}, train_acc={avg_train_acc:.2%}, "
                      f"val_loss={avg_val_loss:.4f}, val_acc={avg_val_acc:.2%}, "
                      f"Φ_C={epoch_metrics['phi_c_coherence']:.4f}")

            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    print(f"⏹️ Early stopping at epoch {epoch}")
                    break

        # Calcular taxa de convergência (exponente β)
        losses = [m['val_loss'] for m in self.training_metrics if m['val_loss'] > 0]
        beta = self._estimate_convergence_rate(losses)

        return {
            'final_train_acc': avg_train_acc,
            'final_val_acc': avg_val_acc,
            'best_val_loss': best_val_loss,
            'convergence_beta': beta,
            'epochs_trained': len(self.training_metrics),
            'phi_c_final_coherence': self.model.phi_c_field.trace().real / self.model.phi_c_field.shape[0],
        }

    def _estimate_convergence_rate(self, losses: List[float], window: int = 10) -> float:
        """Estima expoente de convergência β assumindo lei de potência: loss ~ N^(-β)."""
        if len(losses) < window * 2:
            return 0.0

        # Usar segunda metade para estimar assintótico
        recent_losses = losses[-window:]
        N = np.arange(len(losses) - window + 1, len(losses) + 1)

        # Regressão linear em log-log: log(loss) = -β * log(N) + c
        log_losses = np.log(np.array(recent_losses) + 1e-12)
        log_N = np.log(N)

        beta = -np.polyfit(log_N, log_losses, 1)[0]
        return max(0.0, min(2.0, beta))  # Clamp para valores razoáveis

    def evaluate_on_radix1(self) -> Dict:
        """Avalia modelo no genoma sintético RADIX-1."""
        # Sequência simbólica do RADIX-1
        radix1_seq = "ATGC" * 32 + "GGCC" * 16 + "ATAT" * 16  # 4872 bp simbólico

        pred_class, confidence = self.model.predict(radix1_seq)

        # RADIX-1 é projetado para ser resistente → label esperado = 1
        expected_label = 1
        correct = (pred_class == expected_label)

        return {
            'predicted_class': pred_class,
            'confidence': confidence,
            'expected_label': expected_label,
            'correct': correct,
            'phi_c_coherence': self.model.phi_c_field.trace().real / self.model.phi_c_field.shape[0],
        }

    def save_model(self, path: str):
        """Salva modelo treinado."""
        self.model.save_checkpoint(path)
        print(f"💾 Modelo salvo em: {path}")
