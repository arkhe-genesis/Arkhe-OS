import time
import random

class CouncilIOTA:
    """
    IOTA (Σ) — Conselho Deliberativo.
    Implementa votação sequencial anti-OOM para VMs Oracle ARM de 24GB.
    """
    def __init__(self, model="qwen2.5:14b"):
        self.model = model
        self.seeds = [42, 1337, 2024]
        self.threshold = 2 # Maioria simples (2/3)

    def _llm_vote(self, proposal: str, seed: int):
        """Simula um voto de LLM com descarregamento de memória entre chamadas."""
        print(f"[IOTA] Carregando modelo com seed {seed}...")
        time.sleep(1) # Simula latência de carga
        # Em produção, aqui chamaria o Ollama: ollama.chat(model=self.model, ...)
        # Para o stub, usamos uma heurística baseada no seed e na proposta
        vote_val = random.Random(seed + hash(proposal)).choice([True, True, False])
        print(f"[IOTA] Voto concluído: {'APROVADO' if vote_val else 'REJEITADO'}")
        print(f"[IOTA] Descarregando modelo para liberar RAM...")
        time.sleep(0.5)
        return vote_val

    def deliberate(self, proposal: str) -> str:
        print(f"╔════════════════════════════════════════════════════════════╗")
        print(f"║     IOTA v1.1 — DELIBERAÇÃO DO CONSELHO                   ║")
        print(f"╚════════════════════════════════════════════════════════════╝")
        print(f"Proposta: {proposal}\n")

        votes = []
        for i, seed in enumerate(self.seeds):
            print(f"--- Voto {i+1}/3 ---")
            votes.append(self._llm_vote(proposal, seed))

        approved_count = sum(votes)
        verdict = "APPROVED" if approved_count >= self.threshold else "DENIED"

        print(f"\n════════════════════════════════════════════════════════════")
        print(f"RESULTADO: {verdict} ({approved_count}/{len(self.seeds)})")
        print(f"════════════════════════════════════════════════════════════")
        return verdict

if __name__ == "__main__":
    council = CouncilIOTA()
    council.deliberate("Aumentar threshold de RAM para 23GB?")
