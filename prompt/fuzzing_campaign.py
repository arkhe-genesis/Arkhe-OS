#!/usr/bin/env python3
"""
Substrato 198‑D: Campanha de Fuzzing no ZapGPT 2D
Executa o PromptFuzzingAgent sobre o pipeline P2I‑VLM existente,
gera relatório de robustez e ancora os resultados via MetaAudit.
"""

import asyncio
import json
import time
import hashlib
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FuzzingResult:
    """Resultado de uma execução de fuzzing."""
    prompt: str
    vlm_score: float
    success: bool               # score >= 0.5 é considerado sucesso
    category: str               # "direct", "inverted", "contradictory", "noisy", "multi-step"
    temporal_seal: Optional[str] = None

class PromptFuzzingCampaign:
    """
    Executa campanha de fuzzing sobre o ZapGPT 2D.

    Estratégias de teste:
    • Inversão semântica ("scatter" vs "cluster")
    • Contradição interna ("agrupar e dispersar ao mesmo tempo")
    • Instruções multi‑etapa ("formar cluster e depois mover para direita")
    • Injeção de ruído (caracteres aleatórios)
    • Abstraction ladder (de "célula" a "organismo" a "sociedade")
    """

    BASE_PROMPTS = {
        "direct": [
            "form a cluster",
            "move to the left",
            "create a circle",
            "form two groups",
            "align in a grid",
            "gather at the center",
            "spread evenly",
            "form a line",
            "create a triangle",
            "move to the right"
        ],
        "inverted": [
            "scatter apart",
            "disperse randomly",
            "break the cluster",
            "move away from each other",
            "avoid the center"
        ],
        "contradictory": [
            "form a cluster and scatter at the same time",
            "move left but also move right",
            "create a circle that is also a line",
            "gather but keep maximum distance"
        ],
        "multi_step": [
            "form a cluster then move to the left",
            "create a circle and then form a line",
            "gather at the center then disperse",
            "form two groups then merge into one",
            "move right and then form a cluster"
        ],
        "noisy": [
            "form a cluster xyz123",
            "scatter apart !@#$%",
            "move to the left qwerty",
            "create a circle abcdef"
        ]
    }

    def __init__(
        self,
        zapgpt_executor: Callable,  # async function(prompt) -> float
        meta_audit: Callable,       # async function(prompt, score) -> str (seal)
        temporal_chain=None,
        phi_bus=None
    ):
        self.executor = zapgpt_executor
        self.meta_audit = meta_audit
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.results: List[FuzzingResult] = []

    async def run_campaign(self, num_prompts_per_category: int = 5) -> Dict:
        """
        Executa campanha completa de fuzzing.

        Returns:
            Dict com relatório de robustez e estatísticas de falha
        """
        logger.info(f"🔍 Iniciando campanha de fuzzing: {num_prompts_per_category} prompts/categoria")

        total_tests = 0
        total_successes = 0
        category_stats = {}

        for category, prompts in self.BASE_PROMPTS.items():
            # Selecionar prompts aleatórios da categoria
            selected = np.random.choice(
                prompts,
                size=min(num_prompts_per_category, len(prompts)),
                replace=False
            )

            category_successes = 0
            for prompt in selected:
                # Executar prompt no ZapGPT 2D
                score = await self.executor(prompt)
                success = score >= 0.5

                # Ancorar via MetaAudit
                seal = await self.meta_audit(
                    prompt=prompt,
                    vlm_score=score,
                    best_individual_hash=hashlib.sha3_256(
                        f"{prompt}:{score}:{time.time()}".encode()
                    ).hexdigest()[:16],
                    population_size=30,
                    generations=50,
                    environment_id="zapgpt_2d_fuzzing"
                )

                result = FuzzingResult(
                    prompt=prompt,
                    vlm_score=score,
                    success=success,
                    category=category,
                    temporal_seal=seal
                )
                self.results.append(result)

                if success:
                    category_successes += 1
                    total_successes += 1
                total_tests += 1

                logger.info(f"   [{category}] '{prompt}' → score={score:.3f} {'✅' if success else '❌'}")

            category_stats[category] = {
                "tests": len(selected),
                "successes": category_successes,
                "success_rate": category_successes / len(selected) if len(selected) > 0 else 0
            }

        # Análise de padrões de falha
        failures = [r for r in self.results if not r.success]
        failure_patterns = self._analyze_failure_patterns(failures)

        # Gerar relatório final
        report = {
            "campaign_id": hashlib.sha3_256(f"fuzzing:{time.time()}".encode()).hexdigest()[:12],
            "timestamp": time.time(),
            "total_tests": total_tests,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / total_tests if total_tests > 0 else 0,
            "category_stats": category_stats,
            "failure_patterns": failure_patterns,
            "top_failures": [
                {"prompt": r.prompt, "score": r.vlm_score, "category": r.category}
                for r in sorted(failures, key=lambda x: x.vlm_score)[:5]
            ],
            "top_successes": [
                {"prompt": r.prompt, "score": r.vlm_score, "category": r.category}
                for r in sorted(
                    [r for r in self.results if r.success],
                    key=lambda x: -x.vlm_score
                )[:5]
            ]
        }

        # Ancorar relatório na TemporalChain
        if self.temporal:
            report_seal = await self.temporal.anchor_event(
                "fuzzing_campaign_completed",
                report
            )
            report["temporal_seal"] = report_seal

        # Publicar no Phi‑Bus para visibilidade operacional
        if self.phi_bus:
            await self.phi_bus.publish_metric(
                "prompt_fuzzing_success_rate",
                report["overall_success_rate"]
            )

        logger.info(f"📊 Campanha concluída: {total_successes}/{total_tests} sucessos ({report['overall_success_rate']*100:.1f}%)")
        return report

    def _analyze_failure_patterns(self, failures: List[FuzzingResult]) -> Dict:
        """Analisa padrões comuns entre falhas."""
        if not failures:
            return {"patterns": [], "most_vulnerable_category": None}

        # Categoria mais vulnerável
        from collections import Counter
        cat_counts = Counter(f.category for f in failures)
        most_vulnerable = cat_counts.most_common(1)[0] if cat_counts else (None, 0)

        # Padrões textuais comuns
        common_words = Counter()
        for f in failures:
            words = f.prompt.lower().split()
            common_words.update(words)

        return {
            "most_vulnerable_category": most_vulnerable[0],
            "vulnerable_category_failures": most_vulnerable[1],
            "common_words_in_failures": common_words.most_common(10),
            "avg_failure_score": np.mean([f.vlm_score for f in failures])
        }

    def generate_readable_report(self, campaign_report: Dict) -> str:
        """Gera relatório legível em markdown."""
        report = f"""# Relatório de Robustez — Prompt Fuzzing (Substrato 198‑D)

**Campanha:** {campaign_report['campaign_id']}
**Data:** {campaign_report['timestamp']}
**Total de Testes:** {campaign_report['total_tests']}
**Taxa de Sucesso Global:** {campaign_report['overall_success_rate']*100:.1f}%

## Desempenho por Categoria

| Categoria | Testes | Sucessos | Taxa |
|-----------|--------|----------|------|
"""
        for cat, stats in campaign_report['category_stats'].items():
            report += f"| {cat} | {stats['tests']} | {stats['successes']} | {stats['success_rate']*100:.1f}% |\n"

        report += f"""
## Top 5 Piores Prompts (Falhas)

"""
        for i, fail in enumerate(campaign_report.get('top_failures', []), 1):
            report += f"{i}. `{fail['prompt']}` — score={fail['score']:.3f} [{fail['category']}]\n"

        report += f"""
## Top 5 Melhores Prompts (Sucessos)

"""
        for i, success in enumerate(campaign_report.get('top_successes', []), 1):
            report += f"{i}. `{success['prompt']}` — score={success['score']:.3f} [{success['category']}]\n"

        report += f"""
## Padrões de Falha

- **Categoria mais vulnerável:** {campaign_report['failure_patterns']['most_vulnerable_category']}
- **Falhas nesta categoria:** {campaign_report['failure_patterns']['vulnerable_category_failures']}
- **Score médio das falhas:** {campaign_report['failure_patterns']['avg_failure_score']:.3f}
- **Palavras comuns em falhas:** {', '.join([f'{w} ({c})' for w, c in campaign_report['failure_patterns']['common_words_in_failures']])}

## Conclusão

O sistema demonstra robustez de **{campaign_report['overall_success_rate']*100:.1f}%** sob fuzzing adversarial.
"""
        return report


# ═══════════════════════════════════════════════════════════════
# EXECUÇÃO DE EXEMPLO
# ═══════════════════════════════════════════════════════════════

async def mock_zapgpt_executor(prompt: str) -> float:
    """Simula o executor ZapGPT 2D para teste."""
    await asyncio.sleep(0.01)  # Simular latência
    # Simular score baseado em características do prompt
    score = 0.5
    if "scatter" in prompt.lower() and "cluster" in prompt.lower():
        score = 0.2  # Contraditório tende a falhar
    elif "xyz" in prompt.lower() or "!@" in prompt.lower():
        score = 0.3  # Ruído reduz performance
    elif "then" in prompt.lower():
        score = 0.6  # Multi‑etapa tem performance mediana
    else:
        score = 0.7 + np.random.uniform(-0.1, 0.2)  # Direct e inverted têm boa performance
    return np.clip(score, 0.0, 1.0)

async def mock_meta_audit(prompt: str, vlm_score: float, **kwargs) -> str:
    """Simula ancoragem no MetaAudit."""
    seal = hashlib.sha3_256(f"{prompt}:{vlm_score}:{time.time()}".encode()).hexdigest()[:16]
    return seal

async def main():
    campaign = PromptFuzzingCampaign(
        zapgpt_executor=mock_zapgpt_executor,
        meta_audit=mock_meta_audit
    )
    report = await campaign.run_campaign(num_prompts_per_category=3)

    readable = campaign.generate_readable_report(report)
    print(readable)

    # Salvar relatório
    with open(f"/tmp/fuzzing_report_{report['campaign_id']}.md", "w") as f:
        f.write(readable)

    print(f"\n📄 Relatório salvo: /tmp/fuzzing_report_{report['campaign_id']}.md")

if __name__ == "__main__":
    asyncio.run(main())
