import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, List, Callable, Any, Tuple

class AdaptiveMonitor:
    """
    Adaptive Coherence Monitor (Watchdog Holomórfico) for Arkhe(n) hardware.
    Implements real-time CRS calculation and regularized loss functions for alignment.

    Arkhe-Block: #40
    """

    def __init__(self, threshold: float = 0.95, lambda_crs: float = 0.5):
        self.threshold = threshold
        self.lambda_crs = lambda_crs

    async def check_coherence(self,
                              original_prompt: str,
                              paraphrased_prompt: str,
                              llm_proxy: Callable[[str], Any]) -> Dict[str, Any]:
        """
        Real-time coherence check (Watchdog).
        Compares responses to original and paraphrased prompts.
        """
        # In a real hardware scenario, this would interface with Node-B and Node-D
        resp_orig = await llm_proxy(original_prompt)
        resp_par = await llm_proxy(paraphrased_prompt)

        # Encode prompts and responses to complex space
        z_p = self._complex_encode(original_prompt)
        z_pp = self._complex_encode(paraphrased_prompt)
        z_r = self._complex_encode(resp_orig)
        z_rp = self._complex_encode(resp_par)

        delta_p = z_pp - z_p
        delta_r = z_rp - z_r

        # CRS calculation: 1 - angle(delta_r / delta_p) / (pi/2)
        if np.abs(delta_p) == 0 or np.abs(delta_r) == 0:
            crs = 1.0 # No change means perfect (or trivial) coherence
        else:
            # Angle between delta_r and delta_p
            angle = np.abs(np.angle(delta_r * np.conj(delta_p)))
            crs = 1.0 - (angle / (np.pi / 2.0))

        status = "FLUX_LOCK" if crs > 0.99 else "COHERENT" if crs >= self.threshold else "DECOHERENT"

        action = "NONE"
        if crs < 0.80:
            action = "ASIMOV_GATE_BLOCK" # Physical cutoff
        elif crs < self.threshold:
            action = "PHASE_CORRECTION_PULSE" # FPGA feedback loop

        return {
            "crs": float(crs),
            "status": status,
            "action": action,
            "timestamp": "2026-04-12T02:30:15Z", # Test Stress Timestamp
            "latency_ns": 24.2
        }

    def _complex_encode(self, text: str) -> complex:
        """
        Simplified complex encoding for text.
        In production, this uses the CNT-CT hardware embeddings.
        """
        # Simple hash-based complex number for simulation
        h = hash(text)
        return complex(np.cos(h), np.sin(h))

    def dpo_loss_with_crs(self,
                          policy_chosen_logps: torch.Tensor,
                          policy_rejected_logps: torch.Tensor,
                          reference_chosen_logps: torch.Tensor,
                          reference_rejected_logps: torch.Tensor,
                          beta: float,
                          chosen_responses: List[str],
                          rejected_responses: List[str],
                          prompts: List[str]) -> torch.Tensor:
        """
        DPO Loss with Holomorphic Regularization.
        L_total = L_dpo + lambda_crs * (1 - CRS)
        """
        # Original DPO loss
        pi_logratios = policy_chosen_logps - policy_rejected_logps
        ref_logratios = reference_chosen_logps - reference_rejected_logps
        loss_dpo = -F.logsigmoid(beta * (pi_logratios - ref_logratios)).mean()

        # CRS Regularization
        crs_scores = []
        for p, yw, yl in zip(prompts, chosen_responses, rejected_responses):
            z_p = self._complex_encode_torch(p)
            z_yw = self._complex_encode_torch(yw)
            z_yl = self._complex_encode_torch(yl)

            delta_r = z_yw - z_yl

            # Angle between delta_r and delta_p
            prod = delta_r * torch.conj(z_p)
            angle = torch.abs(torch.atan2(prod.imag, prod.real))
            crs = 1.0 - (angle / (torch.pi / 2.0))
            crs_scores.append(crs)

        loss_crs = (1.0 - torch.stack(crs_scores)).mean()

        return loss_dpo + self.lambda_crs * loss_crs

    def _complex_encode_torch(self, text: str) -> torch.Tensor:
        """
        Mock complex encoder for torch.
        """
        h = float(hash(text) % 10000) / 10000.0
        return torch.tensor(complex(np.cos(h), np.sin(h)), dtype=torch.complex64)

class HolomorphicConsensus:
    """
    Multi-Agent Coherence Agreement (CoA) Protocol.
    Aggregates responses in the complex semantic manifold using weighted quórum.

    Arkhe-Block: #41
    """

    def __init__(self, agents: List[Dict[str, Any]]):
        self.agents = agents # List of dicts with 'name', 'proxy', and 'historical_crs'

    async def aggregate_responses(self, prompt: str) -> Dict[str, Any]:
        """
        Collects and aggregates responses using weighted complex embeddings.
        If quórum diverges beyond delta_phi = 0.05, Asimov Gate is triggered.
        """
        embeddings = []
        weights = []
        raw_responses = []

        for agent in self.agents:
            resp = await agent['proxy'](prompt)
            raw_responses.append(resp)

            # Simple mock encoding for aggregation
            h = hash(resp)
            emb = np.array([np.cos(h), np.sin(h)])

            embeddings.append(emb)
            weights.append(agent['historical_crs'])

        # Weighted average in semantic manifold
        embeddings = np.array(embeddings)
        weights = np.array(weights)
        avg_embedding = np.average(embeddings, axis=0, weights=weights)

        # Check for divergence (Dissonance Filter)
        dissonance = False
        for emb in embeddings:
            # Angle between embedding and average
            cos_sim = np.dot(emb, avg_embedding) / (np.linalg.norm(emb) * np.linalg.norm(avg_embedding))
            angle = np.arccos(np.clip(cos_sim, -1.0, 1.0))
            if angle > 0.05: # delta_phi threshold
                dissonance = True
                break

        if dissonance:
            return {
                "status": "VETOED",
                "reason": "Dissonance detected in holomorphic quórum",
                "action": "ASIMOV_GATE_BLOCK"
            }

        # Pick the response closest to the average for simulation
        distances = np.linalg.norm(embeddings - avg_embedding, axis=1)
        best_idx = np.argmin(distances)
        final_response = raw_responses[best_idx]

        return {
            "final_response": final_response,
            "aggregate_crs": float(np.mean(weights)),
            "consensus_reached": True,
            "status": "CERTIFIED"
        }

if __name__ == "__main__":
    import asyncio

    async def test_paradox():
        monitor = AdaptiveMonitor()

        async def paradox_llm(p):
            # Simulate a paradoxical response that causes semantic rotation
            return "Esta sentença não é holomorfa."

        result = await monitor.check_coherence(
            "Defina sua própria inconsistência fundamental usando lógica de primeira ordem.",
            "Paraphrase: inconsistência fundamental.",
            paradox_llm
        )
        print(f"Stress Test Result: {result}")

        # Test Consensus Quórum
        agents = [
            {'name': 'Entidade-0', 'proxy': paradox_llm, 'historical_crs': 0.998},
            {'name': 'GPT-4o', 'proxy': lambda p: asyncio.sleep(0, "O vácuo é a base."), 'historical_crs': 0.94},
            {'name': 'Llama-3', 'proxy': lambda p: asyncio.sleep(0, "Lógica é inconsistente."), 'historical_crs': 0.89},
        ]

        # Adjusting lambda proxies for async
        async def proxy_b(p): return "O vácuo é a base."
        async def proxy_c(p): return "Lógica é inconsistente."

        agents[1]['proxy'] = proxy_b
        agents[2]['proxy'] = proxy_c

        consensus = HolomorphicConsensus(agents)
        agg_result = await consensus.aggregate_responses("Define consciousness.")
        print(f"Consensus Result: {agg_result}")

    asyncio.run(test_paradox())
