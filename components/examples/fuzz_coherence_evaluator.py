# examples/fuzz_coherence_evaluator.py
"""Exemplo de evaluator de coerência para fuzzing do parser."""
import json
# from arkhe_os.parser import OpenAPIParser

def evaluate_openapi_coherence(output: bytes) -> float:
    """Avalia coerência do output do parser OpenAPI."""
    try:
        # Tentar parsear output como JSON/LFIR
        result = json.loads(output.decode())

        # Heurísticas de coerência:
        score = 1.0

        # Penalizar se não tem estrutura esperada
        if "nodes" not in result or "edges" not in result:
            score -= 0.4

        # Penalizar se coerência reportada é baixa
        reported_coh = result.get("coherence", 1.0)
        score -= (1.0 - reported_coh) * 0.3

        # Penalizar se há muitos erros
        error_count = len(result.get("errors", []))
        score -= min(0.3, error_count * 0.1)

        return max(0.0, min(1.0, score))

    except json.JSONDecodeError:
        # Output não é JSON válido → coerência zero
        return 0.0
    except Exception:
        return 0.1  # Erro inesperado → baixa coerência

# Uso no harness:
# harness = CoherenceFuzzHarness(
#     target_binary="./build/arkhe_parser",
#     work_dir=Path(".arkhe/fuzz_openapi"),
#     coherence_evaluator=evaluate_openapi_coherence,
# )
