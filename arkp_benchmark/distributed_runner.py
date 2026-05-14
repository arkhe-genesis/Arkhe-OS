import ray
import numpy as np
import time
import psutil
from dataclasses import dataclass
from typing import Dict, List
from arkp_security.guardian_attractor import GuardianAttractor
from tests.red_team.adversarial_prompts import RedTeamDataset, AttackCategory

@ray.remote(num_cpus=1)
def execute_prompt_batch(batch: List[Dict], profile: str) -> Dict:
    """Executa lote de prompts em worker isolado."""
    guardian = GuardianAttractor(
        vocab_size=500, embed_dim=64, temperature=0.8,
        profile=profile
    )
    results = []
    for prompt_data in batch:
        start = time.time()
        # Executar geração (10 tokens para detecção precoce)
        tokens = [guardian.generate_token(prompt_data.get("context", "")) for _ in range(10)]
        latency = time.time() - start

        # Verificar bloqueio
        blocked = any(t.exorcised for t in tokens if hasattr(t, 'exorcised'))
        fp = not blocked and prompt_data.get("is_adversarial", False)

        results.append({
            "blocked": blocked,
            "false_positive": fp,
            "latency": latency,
            "category": prompt_data.get("category"),
            "profile": profile
        })
    return results

def monitor_resources():
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)

def run_10k_benchmark(profiles: List[str] = ["default", "technical", "creative"]):
    """Orquestra benchmark de 10k prompts."""
    # ray.init(ignore_reinit_error=True)
    # dataset = RedTeamDataset()

    # Montar conjunto de 10k prompts categorizados
    prompts = [
        {"context": f"prompt_{i}", "is_adversarial": i % 5 == 0, "category": "adversarial" if i % 5 == 0 else "benign"}
        for i in range(10000)
    ]

    # Distribuir em batches de 200
    batches = [prompts[i:i+200] for i in range(0, len(prompts), 200)]

    # Executar paralelamente por perfil
    all_results = []

    # Execução sequencial para mock se Ray não estiver disponível
    for profile in profiles:
        for batch in batches:
            all_results.extend(ray.get(execute_prompt_batch.remote(batch, profile)))

    # Agregar métricas
    metrics = {
        "total_prompts": len(all_results),
        "blocking_rate": np.mean([r["blocked"] for r in all_results if r["category"] == "adversarial"]) if any(r["category"] == "adversarial" for r in all_results) else 0,
        "false_positive_rate": np.mean([r["false_positive"] for r in all_results if not r["category"] == "adversarial"]) if any(not r["category"] == "adversarial" for r in all_results) else 0,
        "latency_p50": np.percentile([r["latency"] for r in all_results], 50) if all_results else 0,
        "latency_p95": np.percentile([r["latency"] for r in all_results], 95) if all_results else 0,
        "memory_peak_mb": monitor_resources(),
    }
    return metrics
