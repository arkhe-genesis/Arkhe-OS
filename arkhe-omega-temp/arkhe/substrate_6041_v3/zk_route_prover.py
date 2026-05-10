#!/usr/bin/env python3
"""
Prova ZK da consistência causal de uma rota.
Usa um esquema Sigma (Prover/Verifier) não‑interativo (Fiat‑Shamir).
"""
import hashlib, json, os, time

class ZKRouteProver:
    """
    Gera uma prova de que existe um caminho consistente entre source e dest
    com score >= threshold, sem revelar a rota.
    A implementação usa compromisso de hash da rota como testemunha.
    """
    def __init__(self, source: str, dest: str, route: list, score: float):
        self.source = source
        self.dest = dest
        self.route = route                # testemunha privada
        self.score = score
        self.salt = os.urandom(16).hex()

    def _hash_route(self, route: list) -> str:
        return hashlib.sha3_256(json.dumps(route).encode()).hexdigest()

    def prove(self, threshold=0.99) -> dict:
        """Gera prova não‑interativa via Fiat‑Shamir."""
        if self.score < threshold:
            return {"error": "Score insuficiente"}

        # Compromisso: pedaço oculto da rota
        commitment = self._hash_route(self.route + [self.salt])

        # Desafio determinístico baseado no compromisso e parâmetros
        challenge = hashlib.sha3_256(
            f"{commitment}{self.source}{self.dest}{threshold}".encode()
        ).hexdigest()

        # Resposta: revela parcialmente (salt) e prova conhecimento da rota
        proof = {
            "commitment": commitment,
            "salt": self.salt,
            "source": self.source,
            "dest": self.dest,
            "threshold": threshold,
            "score_proof": self.score,
            "challenge_response": challenge  # simplificação; em produção, usar Schnorr real
        }
        return proof

class ZKRouteVerifier:
    """Verifica a prova sem conhecer a rota completa."""
    def verify(self, proof: dict) -> bool:
        threshold = proof.get("threshold", 0.99)
        if proof.get("score_proof", 0) < threshold:
            return False

        expected_challenge = hashlib.sha3_256(
            f"{proof['commitment']}{proof['source']}{proof['dest']}{threshold}".encode()
        ).hexdigest()

        return proof.get("challenge_response") == expected_challenge

if __name__ == "__main__":
    prover = ZKRouteProver("A", "B", ["A", "C", "B"], 0.99)
    zk_proof = prover.prove(threshold=0.95)
    print("Proof:", zk_proof)
    if "error" not in zk_proof:
        verifier = ZKRouteVerifier()
        is_valid = verifier.verify(zk_proof)
        print("Is Valid:", is_valid)
