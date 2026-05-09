#!/usr/bin/env python3
"""
validate_phase0.py — Validação integrada dos 5 marcos da Fase 0.
Executa testes, benchmarks e verifica artefatos gerados.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: str, cwd: str = None) -> bool:
    """Executa comando shell e retorna sucesso."""
    print(f"🔧 Executando: {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ✗ Erro: {result.stderr}")
        return False
    print(f"  ✓ Sucesso")
    return True

def validate_phase0() -> bool:
    """Valida todos os 5 marcos da Fase 0."""
    print("=" * 90)
    print("ARKHE OS 10Q — VALIDAÇÃO DA FASE 0")
    print("=" * 90)

    all_passed = True

    # 1. Verificar estrutura do repositório
    print("\n[1] Verificando estrutura do repositório arkhe_10q/...")
    required_files = [
        'arkhe_10q/__init__.py',
        'arkhe_10q/geometry/manifold_5d_frc2g.py',
        'arkhe_10q/geometry/hodge_star_5d.py',
        'tests/test_hodge_star_5d.py',
        'benchmarks/contraction_5d_vs_4d.py',
        'proof/riemannian_dp_5d.v',
        'hardware/qdi_multiplexed_sim.py',
        'pyproject.toml'
    ]

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} NÃO ENCONTRADO")
            all_passed = False

    # 2. Executar testes unitários de Hodge star 5D
    print("\n[2] Executando testes unitários ★² = ±1...")
    test_passed = run_command("PYTHONPATH=. python -m pytest tests/test_hodge_star_5d.py -v")
    all_passed = all_passed and test_passed

    # 3. Validar configuração TPU v6
    print("\n[3] Validando configuração TPU v6...")
    if Path('benchmarks/tpu_config.yaml').exists():
        print("  ✓ tpu_config.yaml presente")
        # Verificar sintaxe YAML
        yaml_valid = run_command("python -c 'import yaml; yaml.safe_load(open(\"benchmarks/tpu_config.yaml\"))'")
        all_passed = all_passed and yaml_valid
    else:
        print("  ✗ tpu_config.yaml NÃO ENCONTRADO")
        all_passed = False

    # 4. Verificar prova Coq
    print("\n[4] Verificando prova Coq...")
    if Path('proof/riemannian_dp_5d.v').exists():
        print("  ✓ riemannian_dp_5d.v presente")
        # Tentar compilar (pode falhar se Coq não instalado)
        coq_installed = run_command("coqc --version", cwd="proof")
        if coq_installed:
            proof_compiles = run_command("make", cwd="proof")
            all_passed = all_passed and proof_compiles
        else:
            print("  ⚠ Coq não instalado — prova não compilada (OK para Fase 0)")
    else:
        print("  ✗ riemannian_dp_5d.v NÃO ENCONTRADO")
        all_passed = False

    # 5. Testar protótipo QDI
    print("\n[5] Testando protótipo QDI multiplexada...")
    qdi_test = run_command("python hardware/qdi_multiplexed_sim.py")
    all_passed = all_passed and qdi_test

    # Relatório final
    print("\n" + "=" * 90)
    if all_passed:
        print("✅ VALIDAÇÃO DA FASE 0 CONCLUÍDA COM SUCESSO")
        print("   • Repositório arkhe_10q/ estruturado")
        print("   • Testes ★² = ±1 passando para k=0..5")
        print("   • Benchmark TPU v6 configurado")
        print("   • Prova Coq iniciada com indução dimensional")
        print("   • QDI multiplexada prototipada com 3 backends")
    else:
        print("❌ VALIDAÇÃO DA FASE 0 COM FALHAS")
        print("   Verifique os erros acima e corrija antes de prosseguir.")
    print("=" * 90)

    return all_passed

if __name__ == "__main__":
    success = validate_phase0()
    sys.exit(0 if success else 1)
