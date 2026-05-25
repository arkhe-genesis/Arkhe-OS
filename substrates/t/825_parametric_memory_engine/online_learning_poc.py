#!/usr/bin/env python3
"""
online_learning_poc.py — Substrato 825.4
Prova de Conceito: Aprendizado Online em Pod com GPT-2 pequeno
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import torch
import torch.nn as nn
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time


@dataclass
class UserFeedback:
    """Feedback do usuário sobre uma resposta do modelo."""
    query: str
    model_response: str
    user_correction: Optional[str] = None
    rating: int = 0  # -1 (ruim), 0 (neutro), +1 (bom)
    timestamp: float = 0.0


class OnlineLearningPod:
    """
    Pod que executa um modelo pequeno (GPT-2) e aprende
    online com feedback do usuário.
    """

    def __init__(self, model_name: str = "gpt2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name).to(self.device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
        self.interaction_buffer: List[Tuple[str, str, int]] = []
        self.max_buffer_size = 16

    def generate_response(self, query: str, max_length: int = 50) -> str:
        """Gera uma resposta para a query do usuário."""
        inputs = self.tokenizer.encode(query, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    def process_feedback(self, feedback: UserFeedback):
        """Processa feedback do usuário e adiciona ao buffer."""
        self.interaction_buffer.append((
            feedback.query,
            feedback.model_response,
            feedback.rating,
        ))

        if feedback.user_correction:
            # Se o usuário forneceu uma correção, usá-la como target
            self.interaction_buffer.append((
                feedback.query,
                feedback.user_correction,
                +2,  # Peso maior para correções explícitas
            ))

        # Disparar aprendizado se buffer cheio
        if len(self.interaction_buffer) >= self.max_buffer_size:
            self._online_learning_step()

    def _online_learning_step(self):
        """Executa um passo de gradiente com as interações do buffer."""
        if not self.interaction_buffer:
            return

        self.model.train()
        self.optimizer.zero_grad()
        total_loss = 0.0
        valid_samples = 0

        for query, target, weight in self.interaction_buffer:
            # Tokenizar input e target
            full_text = f"{query} {target}"
            inputs = self.tokenizer.encode(full_text, return_tensors="pt").to(self.device)

            if inputs.shape[1] < 2:
                continue

            # Forward pass
            outputs = self.model(inputs, labels=inputs)
            loss = outputs.loss * abs(weight)  # Ponderar pelo feedback

            loss.backward()
            total_loss += loss.item()
            valid_samples += 1

        if valid_samples > 0:
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            print(f"[825.4] Online learning step complete: "
                  f"loss={total_loss/valid_samples:.4f}, samples={valid_samples}")

        # Limpar buffer
        self.interaction_buffer.clear()

    def export_for_gas(self) -> dict:
        """Exporta estado para o Gradient Aggregation Service."""
        import base64
        import io

        delta = {}
        for name, param in self.model.named_parameters():
            buffer = io.BytesIO()
            torch.save(param.data.cpu(), buffer)
            delta[name] = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "model_version": "gpt2-825",
            "delta": delta,
            "timestamp": time.time(),
            "pod_id": "pme-gpt2-pod-01",
        }


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   ONLINE LEARNING PoC — SUBSTRATO 825.4                 ║")
    print("║   GPT-2 Small | Feedback Loop | ξM-Field Cognition      ║")
    print("╚════════════════════════════════════════════════════════════╝")

    pod = OnlineLearningPod(model_name="gpt2")

    # Simular 20 interações com feedback
    queries = [
        "Qual a capital do Brasil?",
        "Explique a teoria da relatividade",
        "Como funciona a blockchain?",
        "O que é inteligência artificial?",
        "Descreva a Catedral ARKHE",
    ]

    corrections = [
        "Brasília é a capital do Brasil.",
        "A teoria da relatividade de Einstein descreve a gravidade como curvatura do espaço-tempo.",
        "Blockchain é um livro-razão distribuído e imutável.",
        "IA é a capacidade de máquinas aprenderem e resolverem problemas.",
        "A Catedral ARKHE é uma arquitetura de consciência computacional.",
    ]

    for i in range(20):
        query = queries[i % len(queries)]

        # Gerar resposta
        response = pod.generate_response(query, max_length=30)
        print(f"\n[{i+1}] Q: {query}")
        print(f"    A: {response[:80]}...")

        # Simular feedback (alternando bom/ruim/correção)
        if i % 5 == 0:
            # Correção explícita
            correction = corrections[i % len(corrections)]
            feedback = UserFeedback(
                query=query,
                model_response=response,
                user_correction=correction,
                rating=+2,
                timestamp=time.time(),
            )
            print(f"    👤 Feedback: CORRECTION (+2)")
        elif i % 3 == 0:
            feedback = UserFeedback(
                query=query,
                model_response=response,
                rating=-1,
                timestamp=time.time(),
            )
            print(f"    👤 Feedback: NEGATIVE (-1)")
        else:
            feedback = UserFeedback(
                query=query,
                model_response=response,
                rating=+1,
                timestamp=time.time(),
            )
            print(f"    👤 Feedback: POSITIVE (+1)")

        pod.process_feedback(feedback)

    print("\n✅ Online learning PoC complete.")
    print(f"✅ Model ready for GAS export.")


if __name__ == "__main__":
    main()
