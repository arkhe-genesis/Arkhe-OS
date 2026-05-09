#!/usr/bin/env python3
"""
FASE 1 — VALIDAÇÃO EMPÍRICA COMPLETA (HCP‑AGING)
Script executável de ponta a ponta para testar as hipóteses do NeuralScaffold
com dados reais do Human Connectome Project – Aging.

Uso:
    python run_hcp_validation.py --subjects HCA6002236 HCA6002237 ...
                                 --output_dir ./results
                                 --credentials ~/.hcp_credentials.json
                                 --download   (opcional, se os dados ainda não estiverem locais)
"""

import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import List, Dict

# Importa os módulos definidos anteriormente
# Adiciona src ao PYTHONPATH para garantir que os imports funcionem
sys.path.append(str(Path(__file__).parent / "src"))
from neuro.hcp_validator import HCPAgingValidator

# ------------------------------------------------------------
# 1. Funções de análise estatística e visualização
# ------------------------------------------------------------
def run_statistical_tests(df: pd.DataFrame) -> Dict:
    """Aplica os testes H1-H3 e retorna sumário."""
    results = {}

    # H1: ANOVA entre grupos diagnósticos (CN, MCI, MCI_AD)
    groups = [df[df['diagnosis'] == d]['r_global'].dropna().values
              for d in ['CN', 'MCI', 'MCI_AD'] if d in df['diagnosis'].unique()]
    if len(groups) >= 2:
        f_stat, p_val = stats.f_oneway(*groups)
        results['H1_ANOVA_F'] = f_stat
        results['H1_ANOVA_p'] = p_val
        results['H1_supported'] = p_val < 0.05
    else:
        results['H1_supported'] = False

    # H2: Correlação entre r_global e MoCA (ou CogComposite)
    if 'moca' in df.columns and df['moca'].notna().any():
        corr, p = stats.spearmanr(df['r_global'], df['moca'], nan_policy='omit')
        results['H2_metric'] = 'MoCA'
        results['H2_correlation'] = corr
        results['H2_p'] = p
        results['H2_supported'] = (corr > 0) and (p < 0.05)
    elif 'cog_composite' in df.columns and df['cog_composite'].notna().any():
        corr, p = stats.spearmanr(df['r_global'], df['cog_composite'], nan_policy='omit')
        results['H2_metric'] = 'CogComposite'
        results['H2_correlation'] = corr
        results['H2_p'] = p
        results['H2_supported'] = (corr > 0) and (p < 0.05)
    else:
        results['H2_supported'] = False

    # H3: Correlação entre X_eff e severidade (CDR não disponível, usar MoCA invertido)
    if 'moca' in df.columns and df['moca'].notna().any():
        # MoCA menor = maior severidade
        severity = -df['moca']
        corr, p = stats.spearmanr(df['X_eff_volume'], severity, nan_policy='omit')
        results['H3_correlation'] = corr
        results['H3_p'] = p
        results['H3_supported'] = (corr > 0) and (p < 0.05)
    else:
        results['H3_supported'] = False

    return results

def generate_report(df: pd.DataFrame, stats: Dict, output_dir: Path):
    """Gera visualizações e salva relatório."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Figura 1: Boxplot e scatter
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # r por diagnóstico
    ax = axes[0, 0]
    if not df.empty and 'diagnosis' in df.columns and 'r_global' in df.columns:
        df.boxplot(column='r_global', by='diagnosis', ax=ax)
    ax.set_title('Parâmetro de Ordem (r) por Diagnóstico')
    ax.set_ylabel('r_global')

    # r vs MoCA
    ax = axes[0, 1]
    if 'moca' in df.columns:
        for diag, color in zip(['CN', 'MCI', 'MCI_AD'], ['green', 'orange', 'red']):
            subset = df[df['diagnosis'] == diag]
            if not subset.empty:
                ax.scatter(subset['moca'], subset['r_global'], c=color, label=diag, alpha=0.7)
        ax.set_xlabel('MoCA')
        ax.set_ylabel('r_global')
        ax.legend()
        ax.set_title(f"r × MoCA (ρ={stats.get('H2_correlation', 0):.2f})")

    # X_eff vs severidade
    ax = axes[1, 0]
    if 'moca' in df.columns:
        severity = 30 - df['moca']  # 30 = max MoCA
        ax.scatter(severity, df['X_eff_volume'], c=df['r_global'], cmap='viridis', alpha=0.7)
        ax.set_xlabel('Severidade (30 - MoCA)')
        ax.set_ylabel('X_eff (entropia)')
        ax.set_title(f"X_eff × Severidade (ρ={stats.get('H3_correlation', 0):.2f})")

    # Histórico de degradação
    ax = axes[1, 1]
    if 'degradation_calibrated' in df.columns:
        ax.hist(df['degradation_calibrated'], bins=20, alpha=0.7)
    ax.set_xlabel('Degradação Calibrada')
    ax.set_ylabel('Frequência')
    ax.set_title('Distribuição de Degradação Estimada')

    plt.tight_layout()
    plt.savefig(output_dir / 'hcp_validation_plots.png', dpi=150)
    plt.close()

    # Salvar CSV
    df.to_csv(output_dir / 'processed_subjects.csv', index=False)

    # Relatório textual
    with open(output_dir / 'statistical_report.txt', 'w') as f:
        f.write("RELATÓRIO DE VALIDAÇÃO HCP‑AGING\n")
        f.write("="*50 + "\n")
        f.write(f"Número de sujeitos processados: {len(df)}\n")
        if 'diagnosis' in df.columns:
            f.write(f"Diagnósticos: {dict(df['diagnosis'].value_counts())}\n\n")

        f.write("HIPÓTESES TESTADAS\n")
        f.write("-"*20 + "\n")
        f.write(f"H1 (diferença entre grupos): {'✓' if stats.get('H1_supported') else '✗'}\n")
        if 'H1_ANOVA_p' in stats:
            f.write(f"   F = {stats['H1_ANOVA_F']:.3f}, p = {stats['H1_ANOVA_p']:.4f}\n")

        f.write(f"\nH2 (correlação r × {stats.get('H2_metric', 'Cognição')}): {'✓' if stats.get('H2_supported') else '✗'}\n")
        if 'H2_correlation' in stats:
            f.write(f"   ρ = {stats['H2_correlation']:.3f}, p = {stats['H2_p']:.4f}\n")

        f.write(f"\nH3 (correlação X_eff × severidade): {'✓' if stats.get('H3_supported') else '✗'}\n")
        if 'H3_correlation' in stats:
            f.write(f"   ρ = {stats['H3_correlation']:.3f}, p = {stats['H3_p']:.4f}\n")

    print(f"Relatório salvo em {output_dir}")

# ------------------------------------------------------------
# 2. Função principal de execução
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Validação NeuralScaffold com dados HCP‑Aging")
    parser.add_argument("--subjects", nargs="+", required=True,
                        help="Lista de IDs de sujeitos (ex: HCA6002236 HCA6002237)")
    parser.add_argument("--data_root", type=str, default="/data/hcp_aging",
                        help="Diretório raiz com os dados HCP")
    parser.add_argument("--output_dir", type=str, default="./results",
                        help="Diretório para salvar resultados")
    parser.add_argument("--credentials", type=str, default=None,
                        help="Arquivo JSON com credenciais AWS")
    parser.add_argument("--download", action="store_true",
                        help="Baixar dados automaticamente (requer credenciais)")
    parser.add_argument("--no_fmri", action="store_true",
                        help="Ignorar fMRI e usar dinâmica sintética")
    args = parser.parse_args()

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Inicializar validador
    validator = HCPAgingValidator(
        data_root=data_root,
        credentials_file=Path(args.credentials) if args.credentials else None
    )

    results = []
    for sid in args.subjects:
        print(f"\nProcessando {sid}...")
        try:
            # Download se solicitado
            if args.download:
                success = validator.download_subject_data(sid, modalities=['structural']
                                                          if args.no_fmri else ['structural', 'functional'])
                if not success:
                    print(f"   ✗ Falha no download de {sid}")
                    continue

            # Carregar e processar
            data = validator.load_subject(sid)

            # Se não houver fMRI, forçar fallback
            if args.no_fmri:
                data['bold_series'] = None

            result = validator.process_subject(data)
            results.append(result)
            print(f"   ✓ r = {result['r_global']:.3f}, "
                  f"MoCA = {result.get('moca', 'N/A')}, "
                  f"Fase = {result['phase']}")

        except Exception as e:
            print(f"   ✗ Erro: {e}")
            continue

    if not results:
        print("Nenhum sujeito processado com sucesso.")
        sys.exit(1)

    # Consolidar resultados
    df = pd.DataFrame(results)
    stats_results = run_statistical_tests(df)
    generate_report(df, stats_results, output_dir)

    # Exibir sumário
    print("\n" + "="*50)
    print("SUMÁRIO DA VALIDAÇÃO")
    print("="*50)
    print(f"Sujeitos processados: {len(df)}")
    print(f"H1 (diferença entre grupos): {'✓' if stats_results.get('H1_supported') else '✗'}")
    print(f"H2 (correlação r × cognição): {'✓' if stats_results.get('H2_supported') else '✗'}")
    print(f"H3 (correlação X_eff × severidade): {'✓' if stats_results.get('H3_supported') else '✗'}")

    if all([stats_results.get('H1_supported'), stats_results.get('H2_supported'), stats_results.get('H3_supported')]):
        print("\n✅ MODELO VALIDADO: As três hipóteses são suportadas pelos dados empíricos.")
    else:
        print("\n⚠️  VALIDAÇÃO PARCIAL: Algumas hipóteses não atingiram significância estatística.")

if __name__ == "__main__":
    main()
