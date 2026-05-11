import os

# Modo Catedral ativado por variável de ambiente
CATHEDRAL_MODE = os.environ.get("ARKHE_CATHEDRAL_MODE", "0") == "1"

def local_llm(prompt: str) -> str:
    # Dummy implementation for local LLM
    return "Dummy response from LLM"

def get_consistency_oracle():
    # Dummy implementation
    class DummyReport:
        def __init__(self):
            self.consistent = True
            self.score = 1.0
            self.paradox_type = None
            self.violations = []

    class DummyOracle:
        def evaluate(self, msg):
            return DummyReport()

    return DummyOracle()

def ask_llm(prompt: str, context: dict = None) -> dict:
    if CATHEDRAL_MODE:
        # Adiciona exigência de verificação
        prompt = (
            "[MODO CATEDRAL] Você é um nó da rede ARKHE Ω‑TEMP v4.1.1. "
            "Toda resposta deve:\n"
            "1. Ser validada pelo ConsistencyOracle (6 checks)\n"
            "2. Incluir referência ao hash do ledger quando aplicável\n"
            "3. Sinalizar qualquer inconsistência detectada\n\n"
            + prompt
        )

    response = local_llm(prompt)  # consulta ao modelo fine‑tunado
    if CATHEDRAL_MODE:
        # Pós‑validação com o oráculo
        oracle = get_consistency_oracle()

        class TemporalMessage:
            def __init__(self, **kwargs):
                pass

        msg = TemporalMessage()
        report = oracle.evaluate(msg)
        if not report.consistent:
            response = (
                "[REJEITADO PELA CATEDRAL] "
                f"Score: {report.score:.4f}, Paradoxo: {report.paradox_type}. "
                "Resposta original suprimida para manter coerência temporal."
            )
    return response