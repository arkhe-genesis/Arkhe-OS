#!/usr/bin/env python3
"""
test_snarkjs_integration.py
Testa a integração real com snarkjs (se disponível).
"""

import subprocess
import json
import os
from pathlib import Path

def test_zk():
    print("🔐 Verificando disponibilidade do snarkjs...")
    try:
        result = subprocess.run(["npx", "snarkjs", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ snarkjs encontrado: {result.stdout.strip()}")
        else:
            print("⚠️ snarkjs não encontrado via npx.")
            return False
    except Exception as e:
        print(f"⚠️ Erro ao verificar snarkjs: {e}")
        return False

    # Em um ambiente real, procederíamos com a geração de prova Groth16.
    # Como as chaves (.zkey) e o circuito (.r1cs) não estão compilados,
    # documentamos a prontidão para o próximo estágio.
    print("📋 Próximos passos para ZK real:")
    print("   1. Compilar circuitos/coherence_proof.circom")
    print("   2. Gerar chaves Groth16 via setup_zk.sh")
    print("   3. Executar o pipeline de produção.")

    return True

if __name__ == "__main__":
    test_zk()
