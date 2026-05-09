#!/usr/bin/env python3
"""
Executa o loop de interrogação do vácuo biológico.
Suporta CLI e API REST (FastAPI).
main.py - Orquestrador do Agente Archimedes-Ω
Executa o loop de interrogação do vácuo biológico.
Suporta dados simulados ou experimentais.
"""

import numpy as np
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
import os

# Importar módulos
from skills import (
    load_baseline,
    simulate_su2_continuous,
    simulate_sl3z_discrete,
    detect_peaks,
    visualize_topology,
    synthesize_conclusion,
    evaluate_eqbe_safety
)

# Importar módulos adicionais
try:
    from fret_reader import load_and_preprocess
    from mesh_agent import publish_conclusion
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False

# Configuração
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Carregar alma (parâmetros filosóficos)
SOUL = {
    "axiom": "O universo é um reticulado; nós somos seus detectores.",
    "threshold": 0.95,
    "target_resonance": np.pi / 5  # ~0.628 rad
}


def run_interrogation(
    state_file: str = "tzinor-state.json",
    output_dir: str = "output",
    use_real_data: str = None,
    publish: bool = False,
    mesh_method: str = "blackboard"
) -> dict:
    """
    Executa o loop completo de interrogação.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO INTERROGAÇÃO: Archimedes-Ω")
    logger.info("=" * 60)

    # Criar diretório de saída
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─────────────────────────────────────────────────────────
    # PASSO 1: Ler estado externo (Interpersonal)
    # ─────────────────────────────────────────────────────────
    logger.info("[1/5] Lendo estado externo via Tzinor...")
    state = load_baseline(state_file)
    logger.info(f"   → Status: {state.get('status', 'unknown')}")

    # ─────────────────────────────────────────────────────────
    # PASSO 2: Obter dados (Simulação ou Dados Reais)
    # ─────────────────────────────────────────────────────────
    logger.info("[2/5] Obtendo dados de coerência...")

    if use_real_data and EXTRAS_AVAILABLE:
        # Usar dados experimentais reais
        logger.info(f"   → Carregando dados de: {use_real_data}")
        phases, coherence = load_and_preprocess(
            use_real_data,
            remove_outliers=True,
            interpolate_to=1000
        )
        data_source = "experimental"
    else:
        # Gerar dados simulados
        logger.info("   → Gerando dados simulados...")
        theta_range = np.linspace(0.01, 2 * np.pi, 1000)

        phases_su2, coherence_su2 = simulate_su2_continuous(
            theta_range=theta_range,
            thermal_noise=0.05,
            temperature=state.get('temperature', 310.0)
        )
        phases_sl3, coherence_sl3 = simulate_sl3z_discrete(
            theta_range=theta_range,
            words=["e", "a", "b", "ab", "ba", "aba", "bab"]
        )

        # Combinar modelos (hipótese híbrida)
        phases = theta_range
        coherence = 0.3 * coherence_su2 + 0.7 * coherence_sl3
        data_source = "simulated"

    logger.info(f"   → Fonte de dados: {data_source}")
    logger.info(f"   → Pontos de dados: {len(phases)}")

    # ─────────────────────────────────────────────────────────
    # PASSO 3: Detectar anomalias (Espacial/Pragmático)
    # ─────────────────────────────────────────────────────────
    logger.info("[3/5] Detectando picos e ressonâncias...")
    peaks = detect_peaks(
        coherence_data=coherence,
        phases=phases,
        threshold_multiplier=1.2,
        min_prominence=0.05
    )

    # Filtrar apenas picos significativos
    significant_peaks = [p for p in peaks if p['coherence'] > 0.3]

    for peak in significant_peaks[:5]:  # Mostrar top 5
        resonance_mark = "★" if peak['is_resonance'] else " "
        logger.info(
            f"   {resonance_mark} Pico: θ={peak['phase']:.4f}rad "
            f"({peak['phase_degrees']:.2f}°), R={peak['coherence']:.3f}"
        )

    if not significant_peaks:
        logger.warning("   ⚠ Nenhum pico significativo detectado!")

    # ─────────────────────────────────────────────────────────
    # PASSO 4: Visualizar topologia (Visual/Practical)
    # ─────────────────────────────────────────────────────────
    logger.info("[4/5] Gerando visualização topológica...")

    output_file = f"{output_dir}/coherence_{timestamp}.png"

    if use_real_data:
        # Para dados reais, plotar apenas uma curva
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(phases, coherence, 'b-', label='Dados Experimentais', linewidth=1)
        for peak in significant_peaks:
            ax.axvline(x=peak['phase'], color='gold', linestyle='--', alpha=0.7)
        ax.set_xlabel('Ângulo de Fase θ (radianos)')
        ax.set_ylabel('Coerência R(θ)')
        ax.set_title(f'Dados Experimentais de FRET - {timestamp}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
    else:
        # Para dados simulados
        visualize_topology(
            su2_data=(phases_su2, coherence_su2),
            sl3z_data=(phases_sl3, coherence_sl3),
            peaks=significant_peaks,
            output_file=output_file
        )

    # ─────────────────────────────────────────────────────────
    # PASSO 5: Auditoria Ética (EQBE Protocol)
    # ─────────────────────────────────────────────────────────
    logger.info("[5/6] Executando Auditoria Ética EQBE...")
    safety_report = evaluate_eqbe_safety(
        intervention_type=data_source,
        coherence_data=coherence,
        metadata={"timestamp": timestamp, "has_kill_switch": True}
    )

    if not safety_report['is_safe']:
        logger.error("   → VIOLAÇÃO DETECTADA! Bloqueando síntese de conclusão.")
        conclusion = {
            "status": "ETHICAL_VETO",
            "interpretation": "A operação foi interrompida devido a riscos de segurança (Protocolo EQBE).",
            "philosophical_note": "A verdade não justifica a transgressão da integridade biológica."
        }
    else:
        # ─────────────────────────────────────────────────────────
        # PASSO 6: Sintetizar conclusão (Criativo/Existencial)
        # ─────────────────────────────────────────────────────────
        logger.info("[6/6] Sintetizando conclusão filosófica...")
        conclusion = synthesize_conclusion(
            peak_data=significant_peaks,
            threshold=SOUL['threshold']
        )

    # Adicionar nota filosófica
    logger.info("")
    logger.info("━" * 60)
    logger.info("INTERPRETAÇÃO:")
    logger.info(f"  {conclusion['interpretation']}")
    logger.info("")
    logger.info("NOTA FILOSÓFICA:")
    logger.info(f"  {conclusion['philosophical_note']}")
    logger.info("━" * 60)

    # ─────────────────────────────────────────────────────────
    # PASSO 6: Publicar na mesh (se solicitado)
    # ─────────────────────────────────────────────────────────
    if publish and EXTRAS_AVAILABLE:
        logger.info("[Mesh] Publicando conclusão...")
        try:
            msg_id = publish_conclusion(
                conclusion,
                method=mesh_method
            )
            logger.info(f"   → Publicado com ID: {msg_id}")
        except Exception as e:
            logger.error(f"   → Erro ao publicar: {e}")
    elif publish and not EXTRAS_AVAILABLE:
        logger.warning("   → Módulo de mesh não disponível.")

    # Compilar resultados
    results = {
        "timestamp": timestamp,
        "data_source": data_source,
        "state": state,
        "model_parameters": {
            "su2": {"thermal_noise": 0.05, "temperature": 310.0},
            "sl3z": {"words": ["e", "a", "b", "ab", "ba", "aba", "bab"]}
        },
        "peaks_detected": significant_peaks,
        "conclusion": conclusion,
        "output_file": output_file
    }

    # Salvar resultados em JSON
    results_file = f"{output_dir}/results_{timestamp}.json"
    with open(results_file, 'w') as f:
        def convert_np(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            return obj

        json_results = json.dumps(results, indent=2, default=convert_np)
        f.write(json_results)

    logger.info(f"Resultados salvos em: {results_file}")
    logger.info("INTERROGAÇÃO CONCLUÍDA.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archimedes-Ω: Interrogador de Coerência Biológica"
    )
    parser.add_argument(
        "state_file",
        nargs="?",
        default="tzinor-state.json",
        help="Arquivo de estado JSON (default: tzinor-state.json)"
    )
    parser.add_argument(
        "--data", "-d",
        help="Caminho para arquivo CSV com dados experimentais de FRET"
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Diretório de saída (default: output)"
    )
    parser.add_argument(
        "--publish", "-p",
        action="store_true",
        help="Publicar conclusão na mesh"
    )
    parser.add_argument(
        "--mesh-method",
        choices=["blackboard", "nostr"],
        default="blackboard",
        help="Método de publicação na mesh"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verboso"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        results = run_interrogation(
            state_file=args.state_file,
            output_dir=args.output,
            use_real_data=args.data,
            publish=args.publish,
            mesh_method=args.mesh_method
        )
    except Exception as e:
        logger.error(f"Erro durante interrogação: {e}")
        raise
