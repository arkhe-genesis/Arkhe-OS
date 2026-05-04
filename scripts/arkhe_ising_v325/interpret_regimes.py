#!/usr/bin/env python3
"""
interpret_regimes.py
Lê os resultados de classificação json e interpreta para orientações arquiteturais.
"""
import json
import argparse
import sys
import os

def load_classification(filepath):
    """Carrega os resultados do pipeline Ising."""
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo {filepath} não encontrado.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        return json.load(f)

def interpret_and_print(results):
    """Interpreta os resultados e imprime as recomendações."""
    print("\n" + "="*60)
    print("🧠 DECRETO DA GEOMETRIA REVELADA — INTERPRETAÇÃO DE REGIMES")
    print("="*60)

    classification = results.get('classification', {})
    if not classification:
        print("❌ Nenhum dado de classificação encontrado no arquivo.")
        return

    print(f"\n📊 Resumo Estatístico:")
    print(f"   • Cristais analisados: {results.get('n_crystals')}")
    print(f"   • Comunidades detectadas: {results.get('n_communities')}")
    print(f"   • Log-Likelihood Ising: {results.get('ising_log_likelihood', 0):.2f}")

    # Contar regimes
    regimes = [data['regime'] for data in classification.values()]
    regime_counts = {r: regimes.count(r) for r in set(regimes)}

    print("\n🔍 Distribuição de Regimes:")
    for regime, count in regime_counts.items():
        print(f"   • {regime}: {count} comunidades")

    # Detalhar por comunidade importante
    print("\n📝 Detalhamento de Comunidades Significativas (n > 5):")
    for cid, data in classification.items():
        if data['size'] > 5:
            print(f"   [Comunidade {cid}] {data['regime']:10s} | Tamanho: {data['size']:3d} | Coesão (ρ): {data['rho']:+.3f}")

    print("\n🎯 RECOMENDAÇÕES ARQUITETURAIS BASEADAS NA GEOMETRIA:")

    if regime_counts.get('CAPTURE', 0) > 0:
        print("\n✅ Regime CAPTURE (ρ ≥ +τ) Detectado")
        print("   O que significa:")
        print("   • Grupos de cristais oscilam de forma coerente, representando um manifold unificado.")
        print("   • Intervenções produzirão mudanças suaves e previsíveis no estado global.")
        print("   Ação recomendada:")
        print("   • MANTER sparsity atual (não aumentar).")
        print("   • EXPLORAR steering: mover-se ao longo do manifold para navegação intencional.")
        print("   • UTILIZAR ZEE200 para provar em ZK que o grupo captura o manifold.")

    if regime_counts.get('SHATTERING', 0) > 0:
        print("\n⚠️ Regime SHATTERING (ρ ≤ -τ) Detectado")
        print("   O que significa:")
        print("   • Cristais atuam como 'tuning curves' locais (fragmentação distribuída).")
        print("   Ação recomendada:")
        print("   • CONSIDERAR AUMENTAR o acoplamento global (κ) para promover capture.")
        print("   • AVALIAR se a fragmentação é desejável (pode ser útil para discriminação fina).")
        print("   • EXPLORAR hierarchical clustering para achar sub-manifolds.")

    if regime_counts.get('DILUTION', 0) > len(classification) * 0.5:
        print("\n❌ Regime DILUTION (|ρ| < τ) Dominante")
        print("   O que significa:")
        print("   • Couplings mistos/fracos. Falta de estrutura coerente clara.")
        print("   • Causa provável: ruído excessivo, sparsity muito baixa ou manifold mal amostrado.")
        print("   Ação recomendada:")
        print("   • AUMENTAR a sparsity do SAE para forçar a seleção de features mais informativas.")
        print("   • REVISAR o threshold de binarização (pode estar capturando ruído).")
        print("   • RE-TREINAR o SAE com regularização L1 mais forte.")

    if regime_counts.get('AMBIGUOUS', 0) > 0:
        print("\n❓ Regime AMBIGUOUS Detectado")
        print("   O que significa:")
        print("   • Zona de transição ou tamanho/coesão no limite dos thresholds.")
        print("   Ação recomendada:")
        print("   • AJUSTAR parâmetros k_manifold_est e tau na pipeline para refinar as fronteiras de decisão.")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interpreta resultados de classificação Ising.")
    parser.add_argument("--classification", type=str, required=True, help="Caminho para o JSON de resultados")

    args = parser.parse_args()
    results = load_classification(args.classification)
    interpret_and_print(results)
