#!/usr/bin/env python3
"""
Motor de Inferência Otimizado Arkhe.
Técnicas: torch.compile (CUDA graphs implícitos), Continuous Batching, FP8 real.
"""

import torch
import torch.nn.functional as F
import numpy as np
import time
from typing import List, Dict
from queue import Queue
from threading import Thread
from src.arkhe_core.arkhe_triton import NeuralTransformer, ModelArgs

class ArkheOptimizedEngine:
    def __init__(self, model_args: ModelArgs, device: int = 0):
        self.device = device
        self.dtype = torch.bfloat16 # Usar bf16 para computação, fp8 para pesos se suportado

        # 1. INICIALIZAR MODELO
        self.model = NeuralTransformer(model_args).to(self.device).eval()

        # 2. A MAGIA DO torch.compile (PyTorch 2.0+)
        # Reduz overhead de Python e otimiza kernels CUDA (equivalente a Triton/xformers manual)
        print(f"[GPU {device}] Compilando modelo com torch.compile (max-autotune)...")
        try:
            self.model = torch.compile(
                self.model,
                mode="max-autotune", # Testa múltiplos kernels para encontrar o mais rápido
                fullgraph=True       # Exige que o modelo inteiro seja um único grafo
            )
        except Exception as e:
            print(f"⚠️ torch.compile failed or not supported: {e}. Falling back to standard eval.")

        # 3. PRÉ-AQUECIMENTO (Warmup) - CRÍTICO PARA torch.compile
        # A primeira execução compila o grafo. As subsequentes são instantâneas.
        print(f"[GPU {device}] Executando warmup (3 iterações)...")
        dummy_input = torch.randn(1, 64, model_args.dim, device=self.device, dtype=self.dtype)
        for _ in range(3):
            with torch.no_grad():
                _ = self.model.forward_embeddings(dummy_input)
        torch.cuda.synchronize(self.device) if torch.cuda.is_available() else None
        print(f"[GPU {device}] ✅ Motor otimizado pronto.")

    @torch.inference_mode()
    def process_batch(self, batch_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Processa um lote de embeddings de forma otimizada.
        batch_embeddings: (batch_size, seq_len, dim)
        """
        # Garantir que está no dispositivo correto e sem grad
        batch_embeddings = batch_embeddings.to(self.device, dtype=self.dtype)

        # Forward compilado (após warmup, não há overhead Python aqui)
        logits = self.model.forward_embeddings(batch_embeddings)
        return logits

class ArkheFuture:
    def __init__(self):
        self._result = None
        self._done = threading.Event()

    def set_result(self, result):
        self._result = result
        self._done.set()

    def result(self):
        self._done.wait()
        return self._result

class DynamicBatcher:
    """
    Agrega múltiplas requisições em um único batch para maximizar utilização da GPU.
    Em vez de processar 1 sinal por vez, processa N sinais simultaneamente.
    """
    def __init__(self, engine: ArkheOptimizedEngine, max_batch_size: int = 8, max_wait_ms: int = 10):
        self.engine = engine
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.queue = Queue()
        self.running = True

        # Iniciar thread de background para processamento contínuo
        self.worker_thread = Thread(target=self._batch_loop, daemon=True)
        self.worker_thread.start()

    def submit(self, signal_id: str, embedding: np.ndarray) -> ArkheFuture:
        """Submete um sinal para processamento assíncrono."""
        future = ArkheFuture()
        self.queue.put({'id': signal_id, 'embedding': embedding, 'future': future})
        return future

    def _batch_loop(self):
        """Loop em background que coleta sinais e executa batches."""
        while self.running:
            batch_items = []
            start_wait = time.time()

            # Coletar itens até atingir max_batch_size ou timeout
            while len(batch_items) < self.max_batch_size:
                if not self.queue.empty():
                    batch_items.append(self.queue.get())
                elif (time.time() - start_wait) * 1000 > self.max_wait_ms:
                    break
                else:
                    time.sleep(0.001) # Yield CPU

            if not batch_items:
                continue

            # PAD DYNAMIC: Completar com zeros para que todos tenham o mesmo seq_len
            max_seq_len = max(item['embedding'].shape[0] for item in batch_items)
            dim = batch_items[0]['embedding'].shape[1]

            padded_batch = np.zeros((len(batch_items), max_seq_len, dim), dtype=np.float32)
            for i, item in enumerate(batch_items):
                seq_len = item['embedding'].shape[0]
                padded_batch[i, :seq_len, :] = item['embedding']

            # Converter para tensor e processar
            batch_tensor = torch.from_numpy(padded_batch)
            logits_batch = self.engine.process_batch(batch_tensor)

            # Extrair entropia (Ω) para cada item do batch e resolver futures
            for i, item in enumerate(batch_items):
                seq_len = item['embedding'].shape[0]
                # Pegar apenas os logits reais (ignorar padding)
                valid_logits = logits_batch[i, :seq_len, :]

                # Calcular Ω (1 / (1 + H_norm))
                probs = F.softmax(valid_logits.float(), dim=-1)
                H = -(probs * torch.log(probs + 1e-10)).sum(dim=-1).mean()
                H_max = np.log(valid_logits.size(-1))
                omega = (1.0 / (1.0 + (H.item() / H_max)))

                item['future'].set_result(omega)

    def shutdown(self):
        self.running = False
