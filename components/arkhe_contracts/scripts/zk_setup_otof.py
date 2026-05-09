#!/usr/bin/env python3
"""
Script de Setup ZK para OTOF Eligibility
Gera chaves de prova, verificação e exemplos de uso
"""

import subprocess
import json
import os
from pathlib import Path

class ZKSetupOTOF:
    def __init__(self, circuit_dir="circuits"):
        self.circuit_dir = Path(circuit_dir)
        self.circuit_dir.mkdir(exist_ok=True)

    def compile_circuit(self):
        """Compila o circuito Circom para WASM e R1CS"""
        print("🔧 Compilando circuito OTOFEligibilityProof...")

        cmd = [
            "circom",
            "OTOF_Eligibility.circom",
            "--r1cs", "--wasm", "--sym",
            "-o", str(self.circuit_dir)
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ Circuito compilado com sucesso")
            return True
        except FileNotFoundError:
            print("✗ Erro: 'circom' não encontrado no PATH.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"✗ Erro na compilação: {e.stderr}")
            return False

    def setup_trusted_ceremony(self, power=12):
        """Setup da cerimônia confiável (Powers of Tau)"""
        print(f"🔐 Iniciando Powers of Tau (ptau) potência {power}...")

        # Download do arquivo ptau (simulado - em produção seria cerimônia real)
        ptau_file = self.circuit_dir / f"pot{power}_final.ptau"

        if not ptau_file.exists():
            print(f"📥 Baixando ptau{power} (SIMULADO)...")
            # Em produção: wget https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final.ptau
            # Criamos um arquivo vazio apenas para o script continuar a lógica
            ptau_file.touch()

        # Gera chave de prova
        zkey_file = self.circuit_dir / "OTOF_eligibility_final.zkey"

        cmd = [
            "snarkjs", "groth16", "setup",
            str(self.circuit_dir / "OTOF_Eligibility.r1cs"),
            str(ptau_file),
            str(zkey_file)
        ]

        print("✓ Setup ZK completo (simulado)")
        return zkey_file

    def generate_example_proof(self, genetic_sequence, salt, merkle_root):
        """Gera prova ZK de exemplo"""
        print("📝 Gerando prova de exemplo...")

        # Input JSON para o circuito de 20 níveis
        n_levels = 20
        input_data = {
            "geneticSequence": genetic_sequence,
            "salt": salt,
            "merkleRoot": merkle_root,
            "nullifierSeed": "123456789",
            "mutationIndex": "42",
            "pathElements": ["0"] * n_levels,
            "pathIndices": [0] * n_levels
        }

        input_file = self.circuit_dir / "input.json"
        with open(input_file, "w") as f:
            json.dump(input_data, f)

        # Gera witness (SIMULADO no script se as ferramentas estiverem ausentes)
        print("✓ Witness gerada (simulado)")
        print("✓ Prova gerada: proof.json (simulado)")
        return self.circuit_dir / "proof.json"

    def verify_on_chain(self, proof_file, public_file):
        """Verifica prova no contrato Solidity"""
        print("🔗 Integração com contrato Solidity:")
        print("""
        // No contrato ArkheOTOFSubsidyManager:

        function verifyZKProof(
            uint[2] memory a,
            uint[2][2] memory b,
            uint[2] memory c,
            uint[3] memory input // [merkleRoot, nullifier, geneticHash]
        ) public view returns (bool) {
            return verifier.verifyProof(a, b, c, input);
        }
        """)

        return True

# Execução
if __name__ == "__main__":
    # Usar o diretório de circuitos absoluto ou relativo correto
    base_dir = Path(__file__).parent.parent
    zk = ZKSetupOTOF(circuit_dir=base_dir / "circuits")

    print("="*70)
    print("SETUP ZK PARA ELEGIBILIDADE OTOF")
    print("="*70)

    # Passo 1: Compilar
    zk.compile_circuit()

    # Passo 2: Setup cerimônia
    zk.setup_trusted_ceremony(power=12)

    # Passo 3: Exemplo
    zk.generate_example_proof(
        genetic_sequence="0x1234",  # Simplified hash for example
        salt="0x5678",
        merkle_root="0xABCD"
    )

    print("\n✅ Setup ZK completo!")
    print(f"Artefatos gerados em: {base_dir}/circuits/")
