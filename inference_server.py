#!/usr/bin/env python3
"""
inference_server.py — v70.5.1
Data Parallel puro para inferência neural distribuída.
Cada GPU processa um sub-batch independente. Sem divisão de sequência.
"""

import os
import json
import time
import asyncio
from multiprocessing import Process, Queue
from typing import Dict, Optional

import torch
import torch.distributed as dist
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.arkhe_core.arkhe_triton import NeuralTransformer, ModelArgs
from arkhe_neural.neural_coherence_pipeline import (
    NeuralSignalProcessor, NeuralTokenizerConfig, compute_omega_from_logits
)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
WORLD_SIZE = int(os.environ.get("WORLD_SIZE", 1))
RANK = int(os.environ.get("RANK", 0))
MASTER_ADDR = os.environ.get("MASTER_ADDR", "localhost")
MASTER_PORT = int(os.environ.get("MASTER_PORT", 29500))

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Fila para comunicação entre API e processo NCCL
task_queue = Queue()
result_queue = Queue()


# ============================================================
# PROCESSO DE INFERÊNCIA (NCCL) — Roda em background
# ============================================================
def inference_worker(rank: int, world_size: int, task_q: Queue, result_q: Queue):
    """Processo isolado para torch.distributed. Não misturar com asyncio."""

    os.environ["CUDA_VISIBLE_DEVICES"] = str(rank)
    try:
        dist.init_process_group(
            backend="nccl" if torch.cuda.is_available() else "gloo",
            init_method=f"tcp://{MASTER_ADDR}:{MASTER_PORT}",
            world_size=world_size,
            rank=rank,
        )
    except Exception as e:
        print(f"⚠️ dist.init_process_group failed: {e}. Running in single-process mode.")

    device = torch.device(f"cuda:0" if torch.cuda.is_available() else "cpu")
    model_args = ModelArgs(
        dim=2048, n_layers=27, n_heads=16, vocab_size=102400,
        dtype="bf16", max_seq_len=4096,
        n_routed_experts=64, n_activated_experts=6,
        moe_inter_dim=1408, kv_lora_rank=512,
        qk_nope_head_dim=128, qk_rope_head_dim=64, v_head_dim=128,
    )

    model = NeuralTransformer(model_args).to(device).eval()
    tokenizer = NeuralSignalProcessor(
        NeuralTokenizerConfig(use_continuous_emb=True), device=device
    )

    print(f"[Worker {rank}] Modelo carregado em {device}")

    while True:
        task = task_q.get()
        if task is None:
            break

        signal = np.array(task["signal"], dtype=np.float32)
        tokens = tokenizer(signal)  # (1, seq_len, dim)

        with torch.inference_mode():
            logits = model.forward_embeddings(tokens, start_pos=0)

        omega = compute_omega_from_logits(logits)

        result = {
            "omega": float(omega.mean().item()),
            "inference_time_ms": 0.0,  # medido no master
            "rank": rank,
            "timestamp": task.get("timestamp"),
        }
        result_q.put(result)

    if dist.is_initialized():
        dist.destroy_process_group()


# ============================================================
# FASTAPI + WEBSOCKET (Async, sem NCCL)
# ============================================================
websocket_clients = []

@app.websocket("/ws/stream")
async def dashboard_stream(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keepalive
    except:
        pass
    finally:
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)

@app.post("/api/v1/infer")
async def infer(payload: dict):
    t0 = time.perf_counter()

    # Enviar tarefa para o worker NCCL
    task_queue.put({
        "signal": payload["signal"],
        "timestamp": time.time(),
    })

    # Aguardar resultado (bloqueia, mas em thread separada do asyncio)
    result = await asyncio.to_thread(result_queue.get)
    result["inference_time_ms"] = (time.perf_counter() - t0) * 1000

    # Broadcast para dashboards
    msg = json.dumps({"type": "coherence_update", "data": result})
    dead = []
    for ws in websocket_clients:
        try:
            await ws.send_text(msg)
        except:
            dead.append(ws)
    for ws in dead:
        websocket_clients.remove(ws)

    return result

@app.get("/health")
async def health():
    return {"status": "ok", "rank": RANK, "world_size": WORLD_SIZE}


# ============================================================
# ENTRYPOINT
# ============================================================
if __name__ == "__main__":
    if RANK == 0:
        # Rank 0 inicia o worker NCCL em processo separado
        p = Process(target=inference_worker, args=(0, WORLD_SIZE, task_queue, result_queue))
        p.start()

        # Iniciar servidor API (async, sem NCCL)
        uvicorn.run(app, host="0.0.0.0", port=8000)

        p.join()
    else:
        # Workers 1-3 rodam apenas o inference_worker
        inference_worker(RANK, WORLD_SIZE, task_queue, result_queue)
