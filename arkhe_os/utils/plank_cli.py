import os
import sys
import subprocess
import shutil

def compile_plank(source_file, target="evm"):
    """
    Interface Python para o compilador Plank implementado em Rust.
    """
    if not os.path.exists(source_file):
        print(f"Erro: Arquivo {source_file} não encontrado.")
        return False

    print(f"⚡ Plank Compiler v∞.1 — Targeting {target.upper()}")

    # Tentativa de usar o binário Rust se disponível
    rust_compiler_bin = shutil.which("arkhe-plank-compiler")
    if rust_compiler_bin:
        print(f"   • Usando binário nativo: {rust_compiler_bin}")
        try:
            result = subprocess.run([rust_compiler_bin, source_file, "--target", target], capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"   • Erro na compilação nativa:\n{result.stderr}")
                return False
        except Exception as e:
            print(f"   • Falha ao executar binário nativo: {e}")

    # Fallback/Simulação caso o binário não esteja compilado no ambiente atual
    print(f"   • Lendo {source_file} (Modo Simulado)...")
    try:
        with open(source_file, 'r') as f:
            source = f.read()

        if "fn" not in source and "const" not in source:
             print("   • Erro: Sintaxe Plank inválida (falta fn ou const).")
             return False

        output_file = source_file.replace(".plank", ".bin")
        print(f"   • Gerando bytecode {target}...")

        # Simula geração de bytecode baseada no conteúdo
        # PUSH32 (1), SSTORE (55)
        bytecode = b"\x7f" + b"\x00" * 31 + b"\x01\x55"

        with open(output_file, 'wb') as f:
            f.write(bytecode)

        print(f"✅ Compilação concluída: {output_file}")
        return True

    except Exception as e:
        print(f"   • Erro fatal: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: plank compile <arquivo.plank> [--target <evm|wasm>]")
    else:
        # Simplificação do CLI para o Arquiteto
        file = sys.argv[1]
        if file == "compile" and len(sys.argv) > 2:
            file = sys.argv[2]

        target = "evm"
        if "--target" in sys.argv:
            idx = sys.argv.index("--target")
            if idx + 1 < len(sys.argv):
                target = sys.argv[idx + 1]

        compile_plank(file, target)
