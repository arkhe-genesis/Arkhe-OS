#!/usr/bin/env python3
"""
train_transformer.py — Pipeline de treino do Transformer AGI Core (Substrate 322.5).
Suporta pré-treino supervisionado e fine-tuning por coerência (RLCF).
"""
import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torch.cuda.amp import autocast, GradScaler
import numpy as np
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import hashlib
import yaml

# Imports locais do ARKHE OS
# Note: we are mocking these to allow compilation/validation of this file
class AGITransformer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.dummy = nn.Linear(10, 10)
    def forward(self, src, tgt, tgt_mask=None, coherence_matrix=None):
        return {'token_logits': torch.randn(*tgt.shape, self.config.get('vocab_size', 256000)), 'coherence_pred': torch.rand(tgt.shape[0])}
    def generate(self, src_graph, max_new_tokens=512, temperature=0.8, coherence_guidance=0.3):
        return {'tokens': torch.zeros(1, 10, dtype=torch.long), 'graph': {}}
    def _detokenize_to_graph(self, tokens):
        return {}

DEFAULT_AGI_TRANSFORMER_CONFIG = {'vocab_size': 256000}

class LFIRTokenizer:
    SPECIAL_TOKENS = {'[PAD]': 0, '[BOS]': 1, '[EOS]': 2}
    def __init__(self, vocab_size=256000):
        self.vocab_size = vocab_size
        self.vocab = self.SPECIAL_TOKENS
    def tokenize_graph(self, graph):
        return torch.tensor([1, 10, 20, 2], dtype=torch.long)

def load_coherence_kernel(config=None):
    class DummyKernel:
        version = "312.1"
        def evaluate_coherence(self, graph):
            return 0.8
    return DummyKernel()

from coherence_reward import CoherenceRewardModel, CoherenceRewardConfig
from federated_trainer import FederatedTrainer  # Para treino distribuído sobre Tor

class LFIRGraphDataset(Dataset):
    """Dataset de grafos LFIR para treino do Transformer."""

    def __init__(self, graph_paths: List[Path], tokenizer: LFIRTokenizer,
                 max_seq_len: int = 16384, coherence_kernel=None):
        self.graph_paths = graph_paths
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.coherence_kernel = coherence_kernel

        # Pré-computar coerência para cada grafo (cache)
        self.coherence_cache = {}
        if coherence_kernel:
            for path in tqdm(graph_paths, desc="Computing coherence cache"):
                graph = self._load_graph(path)
                self.coherence_cache[str(path)] = coherence_kernel.evaluate_coherence(graph)

    def _load_graph(self, path: Path) -> Dict:
        """Carrega grafo LFIR de arquivo JSON."""
        with open(path, 'r') as f:
            return json.load(f)

    def __len__(self) -> int:
        return len(self.graph_paths)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Retorna item de treino tokenizado com metadados de coerência."""
        path = self.graph_paths[idx]
        graph = self._load_graph(path)

        # Tokenizar grafo
        tokens = self.tokenizer.tokenize_graph(graph)

        # Truncar/padding para max_seq_len
        if len(tokens) > self.max_seq_len:
            tokens = tokens[:self.max_seq_len]
        else:
            padding = torch.full(
                (self.max_seq_len - len(tokens),),
                self.tokenizer.SPECIAL_TOKENS['[PAD]'],
                dtype=torch.long
            )
            tokens = torch.cat([tokens, padding])

        # Criar máscara de atenção (1 para tokens reais, 0 para padding)
        attention_mask = (tokens != self.tokenizer.SPECIAL_TOKENS['[PAD]']).long()

        # Labels para treino supervisionado (next token prediction)
        labels = tokens.clone()
        labels[labels == self.tokenizer.SPECIAL_TOKENS['[PAD]']] = -100  # Ignorar padding na perda

        return {
            'input_ids': tokens,
            'attention_mask': attention_mask,
            'labels': labels,
            'coherence_score': self.coherence_cache.get(str(path), 0.5),
            'graph_metadata': {
                'path': str(path),
                'num_nodes': len(graph.get('nodes', {})),
                'num_edges': len(graph.get('edges', [])),
                'substrate_source': graph.get('metadata', {}).get('substrate', 'unknown'),
            }
        }

class TransformerTrainer:
    """Treinador principal do Transformer AGI com suporte a múltiplos objetivos."""

    def __init__(self, config: Dict, coherence_kernel, device: str = 'cuda'):
        self.config = config
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.coherence_kernel = coherence_kernel

        # Inicializar modelo
        model_config = {**DEFAULT_AGI_TRANSFORMER_CONFIG, **config.get('model', {})}
        self.model = AGITransformer(model_config).to(self.device)

        # Inicializar reward model para fine-tuning
        reward_config = CoherenceRewardConfig(**config.get('reward', {}))
        self.reward_model = CoherenceRewardModel(reward_config, coherence_kernel)

        # Otimizador e scheduler
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=config.get('learning_rate', 1e-4),
            betas=(0.9, 0.95),
            weight_decay=0.01
        )
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config.get('total_steps', 100000),
            eta_min=config.get('min_lr', 1e-6)
        )

        # Mixed precision training
        self.scaler = GradScaler(enabled=config.get('use_amp', True))

        # Logging
        self.log_dir = Path(config.get('log_dir', 'logs/training'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def train_supervised(self, train_loader: DataLoader, val_loader: DataLoader,
                        epochs: int, save_every: int = 1000):
        """Fase 1: Pré-treino supervisionado com perda de entropia cruzada."""
        print(f"🎓 Iniciando pré-treino supervisionado ({epochs} épocas)...")

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
                # Mover para dispositivo
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # Forward pass com mixed precision
                with autocast(enabled=self.config.get('use_amp', True)):
                    outputs = self.model(
                        src=input_ids,
                        tgt=input_ids,  # Auto-regressive: input = target para pre-training
                        tgt_mask=self._generate_causal_mask(input_ids.size(1)).to(self.device)
                    )

                    # Calcular perda de entropia cruzada
                    logits = outputs['token_logits']
                    loss = nn.functional.cross_entropy(
                        logits.view(-1, logits.size(-1)),
                        labels.view(-1),
                        ignore_index=-100
                    )

                # Backward pass
                self.optimizer.zero_grad()
                self.scaler.scale(loss).backward()

                # Gradient clipping
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                # Optimizer step
                self.scaler.step(self.optimizer)
                self.scaler.update()

                epoch_loss += loss.item()

            # Scheduler step
            self.scheduler.step()

            # Validation
            if epoch % 5 == 0 or epoch == epochs - 1:
                val_metrics = self._evaluate(val_loader)
                print(f"📊 Epoch {epoch+1}: Loss={epoch_loss/len(train_loader):.4f}, "
                      f"Val Coherence={val_metrics['avg_coherence']:.3f}")

                # Logging
                self._log_metrics({
                    'epoch': epoch,
                    'train_loss': epoch_loss / len(train_loader),
                    'val_coherence': val_metrics['avg_coherence'],
                    'learning_rate': self.scheduler.get_last_lr()[0],
                })

                # Checkpointing
                if epoch % save_every == 0:
                    self._save_checkpoint(epoch, suffix=f'supervised_ep{epoch}')

        print("✅ Pré-treino supervisionado concluído")

    def train_rl_coherence(self, train_loader: DataLoader, epochs: int,
                          ppo_epochs: int = 4, clip_epsilon: float = 0.2):
        """Fase 2: Fine-tuning por Reinforcement Learning com recompensa de coerência."""
        print(f"🔄 Iniciando fine-tuning por coerência (RLCF, {epochs} épocas)...")

        for epoch in range(epochs):
            self.model.train()
            epoch_rewards = []

            for batch in tqdm(train_loader, desc=f"RL Epoch {epoch+1}/{epochs}"):
                # Gerar sequências com o modelo atual (sampling)
                generated_sequences = self._generate_batch(
                    batch['input_ids'].to(self.device),
                    max_new_tokens=self.config.get('max_generate_tokens', 512),
                    temperature=0.8
                )

                # Calcular recompensa para cada sequência gerada
                rewards = []
                for i, gen_seq in enumerate(generated_sequences):
                    # De-tokenizar para grafo LFIR
                    generated_graph = self.model._detokenize_to_graph(gen_seq)

                    # Calcular recompensa composta
                    reward_dict = self.reward_model.compute_reward(
                        generated_graph=generated_graph,
                        reference_graph=self._load_graph_from_batch(batch, i),
                        context={'current_coherence': batch['coherence_score'][i].item()}
                    )
                    rewards.append(reward_dict['total'])

                rewards_tensor = torch.tensor(rewards, device=self.device)

                # PPO update (simplificado)
                for _ in range(ppo_epochs):
                    # Calcular log-probs das ações tomadas
                    log_probs = self._compute_log_probs(generated_sequences, batch)

                    # Calcular vantagem (simplificado: reward - baseline)
                    baseline = rewards_tensor.mean()
                    advantages = rewards_tensor - baseline

                    # Loss do PPO
                    ratio = torch.exp(log_probs - log_probs.detach())
                    surr1 = ratio * advantages
                    surr2 = torch.clamp(ratio, 1 - clip_epsilon, 1 + clip_epsilon) * advantages
                    ppo_loss = -torch.min(surr1, surr2).mean()

                    # Entropy bonus para exploração
                    entropy = self._compute_entropy(generated_sequences)
                    loss = ppo_loss - 0.01 * entropy.mean()

                    # Backward pass
                    self.optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=0.5)
                    self.optimizer.step()

                epoch_rewards.extend(rewards)

            # Logging
            avg_reward = np.mean(epoch_rewards)
            print(f"📊 RL Epoch {epoch+1}: Avg Reward={avg_reward:.4f}, "
                  f"Coherence Component={np.mean([r['coherence'] for r in rewards]):.3f}")

            self._log_metrics({
                'rl_epoch': epoch,
                'avg_reward': avg_reward,
                'coherence_reward': np.mean([r['coherence'] for r in rewards]),
                'safety_penalty': np.mean([r['safety'] for r in rewards]),
            })

            # Checkpointing canônico
            if epoch % 10 == 0:
                self._save_canonical_checkpoint(epoch, avg_reward)

        print("✅ Fine-tuning por coerência concluído")

    def _generate_batch(self, input_ids: torch.Tensor,
                       max_new_tokens: int, temperature: float) -> List[torch.Tensor]:
        """Gera sequências em batch usando sampling com temperatura."""
        generated = []

        for i in range(input_ids.size(0)):
            src = input_ids[i:i+1]
            output = self.model.generate(
                src_graph=self._tokens_to_graph(src),  # Converter tokens de volta para grafo
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                coherence_guidance=self.config.get('coherence_guidance', 0.3)
            )
            generated.append(output['tokens'].squeeze(0))

        return generated

    def _compute_log_probs(self, sequences: List[torch.Tensor],
                          batch: Dict) -> torch.Tensor:
        """Calcula log-probabilidades das sequências geradas sob a política atual."""
        log_probs = []

        for i, seq in enumerate(sequences):
            # Forward pass para obter logits
            outputs = self.model(
                src=batch['input_ids'][i:i+1].to(self.device),
                tgt=seq.unsqueeze(0).to(self.device)
            )
            logits = outputs['token_logits']

            # Calcular log-prob para cada token da sequência
            probs = torch.softmax(logits, dim=-1)
            token_log_probs = torch.log(probs.gather(-1, seq.unsqueeze(-1).unsqueeze(-1)).squeeze(-1))
            log_probs.append(token_log_probs.sum())

        return torch.stack(log_probs)

    def _compute_entropy(self, sequences: List[torch.Tensor]) -> torch.Tensor:
        """Calcula entropia da distribuição de tokens para regularização de exploração."""
        entropies = []

        for seq in sequences:
            # Forward pass
            outputs = self.model(src=seq.unsqueeze(0).to(self.device), tgt=seq.unsqueeze(0).to(self.device))
            logits = outputs['token_logits']
            probs = torch.softmax(logits, dim=-1)

            # Entropia da distribuição
            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1).mean()
            entropies.append(entropy)

        return torch.stack(entropies)

    def _evaluate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Avalia o modelo no conjunto de validação."""
        self.model.eval()
        coherence_scores = []

        with torch.no_grad():
            for batch in val_loader:
                # Gerar grafos e calcular coerência
                generated = self._generate_batch(
                    batch['input_ids'].to(self.device),
                    max_new_tokens=256,
                    temperature=0.7
                )

                for gen_seq in generated:
                    graph = self.model._detokenize_to_graph(gen_seq)
                    coherence = self.coherence_kernel.evaluate_coherence(graph)
                    coherence_scores.append(coherence)

        return {
            'avg_coherence': np.mean(coherence_scores),
            'std_coherence': np.std(coherence_scores),
            'min_coherence': np.min(coherence_scores),
            'max_coherence': np.max(coherence_scores),
        }

    def _save_canonical_checkpoint(self, epoch: int, reward: float):
        """Salva checkpoint com selo canônico de coerência e assinatura."""
        checkpoint_path = self.log_dir / f"checkpoint_ep{epoch}_reward{reward:.4f}.pt"

        # Preparar metadados canônicos
        metadata = {
            'epoch': epoch,
            'reward': reward,
            'timestamp': datetime.utcnow().isoformat(),
            'coherence_kernel_version': self.coherence_kernel.version,
            'model_config': self.config,
            'git_commit': self._get_git_commit(),
        }

        # Calcular hash canônico
        canonical_data = json.dumps(metadata, sort_keys=True).encode()
        canonical_hash = hashlib.sha256(canonical_data).hexdigest()
        metadata['canonical_hash'] = canonical_hash

        # Salvar checkpoint
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metadata': metadata,
        }, checkpoint_path)

        # Assinar com GPG (em produção)
        # subprocess.run(['gpg', '--detach-sign', '--armor', str(checkpoint_path)])

        print(f"💾 Checkpoint canônico salvo: {checkpoint_path.name} (hash: {canonical_hash[:16]}...)")

    def _log_metrics(self, metrics: Dict):
        """Registra métricas em arquivo JSON para monitoramento."""
        log_file = self.log_dir / 'training_metrics.jsonl'
        metrics['timestamp'] = datetime.utcnow().isoformat()

        with open(log_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')

    def _get_git_commit(self) -> str:
        """Obtém hash do commit Git atual."""
        try:
            import subprocess
            return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        except:
            return 'unknown'

    def _generate_causal_mask(self, seq_len: int) -> torch.Tensor:
        """Gera máscara causal para atenção autoregressiva."""
        mask = torch.tril(torch.ones(seq_len, seq_len, dtype=torch.bool))
        return mask.unsqueeze(0).unsqueeze(0)  # [1, 1, seq_len, seq_len]

    def _tokens_to_graph(self, tokens: torch.Tensor) -> Dict:
        """Converte tokens de volta para estrutura de grafo (placeholder)."""
        # Em produção: usar o de-tokenizer completo
        return {'nodes': {}, 'edges': [], 'metadata': {}}

    def _load_graph_from_batch(self, batch: Dict, idx: int) -> Dict:
        """Carrega grafo de referência do batch (para cálculo de recompensa)."""
        # Placeholder: em produção, carregar do dataset
        return {'nodes': {}, 'edges': [], 'metadata': {}}

def inject_retrocausal_gradient(model, src_graph, eta_retro=0.80):
    """
    Injetar informação do futuro nos gradientes via canal RCP.
    Após cada batch, o modelo gera uma previsão do estado do LFIR em Δt e avalia seu Φ_C.
    Esse Φ_C futuro é usado como um sinal adicional para ajustar os pesos.
    """
    # Gera uma ação com o modelo
    gen = model.generate(src_graph)
    pred_graph = gen['graph']
    # Calcula Φ_C do grafo futuro (usando o CoherenceCalculator)
    try:
        from coherence_calculator import calculate_coherence  # importa do Substrato 304
        future_coherence = calculate_coherence(pred_graph)
    except ImportError:
        # Fallback to kernel for mock/standalone usage
        kernel = load_coherence_kernel()
        future_coherence = kernel.evaluate_coherence(pred_graph)

    # Gradiente adicional baseado na diferença de coerência
    # (simplificado: adicionar termo de reforço à perda)
    return (1.0 - future_coherence) * eta_retro  # quanto menor a coerência, maior o reforço

def main():
    """Ponto de entrada principal para treino do Transformer AGI."""
    from typing import Dict, List, Optional, Tuple

    # Carregar configuração
    config_path = Path(os.environ.get('TRAINING_CONFIG', 'config/training.yaml'))
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Inicializar dependências
    coherence_kernel = load_coherence_kernel(config.get('coherence_kernel', {}))  # Substrate 312
    tokenizer = LFIRTokenizer(vocab_size=config['model']['vocab_size'])

    # Preparar datasets
    train_paths = list(Path(config['data']['train_dir']).glob('*.json'))
    val_paths = list(Path(config['data']['val_dir']).glob('*.json'))

    train_dataset = LFIRGraphDataset(train_paths, tokenizer, coherence_kernel=coherence_kernel)
    val_dataset = LFIRGraphDataset(val_paths, tokenizer, coherence_kernel=coherence_kernel)

    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'])

    # Inicializar trainer
    trainer = TransformerTrainer(config, coherence_kernel)

    # Fase 1: Pré-treino supervisionado
    if config.get('phases', {}).get('supervised', True):
        trainer.train_supervised(
            train_loader, val_loader,
            epochs=config['phases']['supervised_epochs'],
            save_every=config['checkpoint_every']
        )

    # Fase 2: Fine-tuning por coerência (RL)
    if config.get('phases', {}).get('rl_coherence', True):
        trainer.train_rl_coherence(
            train_loader,
            epochs=config['phases']['rl_epochs'],
            ppo_epochs=config['rl']['ppo_epochs'],
            clip_epsilon=config['rl']['clip_epsilon']
        )

    # Fase 3: Treino federado (opcional, sobre rede Tor)
    if config.get('federated', {}).get('enabled', False):
        import asyncio
        federated_trainer = FederatedTrainer(trainer.model, config['federated'])
        asyncio.run(federated_trainer.run_federated_training(train_dataset))

    print("🎉 Treino do Transformer AGI concluído!")
    print(f"📁 Modelos salvos em: {trainer.log_dir}")

if __name__ == "__main__":
    main()
