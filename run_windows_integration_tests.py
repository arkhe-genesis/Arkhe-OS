import subprocess
import sys

SCRIPTS = [
    "substrato_6189_wsa_arkhe_field.py",
    "substrato_6190_windows_arm64.py",
    "substrato_6191_windows_dev_home.py",
    "substrato_6192_windows_npu_directml.py",
]

def run_test(script_name):
    print(f"\n[{script_name}] Iniciando execução...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"✅ {script_name} executado com sucesso.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    print("🚀 ARKHE Ω-TEMP v7.6.4 - Validando Integração Windows 11 Expandida")
    print("=" * 60)

    success_count = 0

    for script in SCRIPTS:
        if run_test(script):
            success_count += 1

    print("=" * 60)
    print(f"📊 Resultado Final: {success_count}/{len(SCRIPTS)} testes passaram.")
    if success_count == len(SCRIPTS):
        print("✅ A integração Windows 11 Expandida está canonicamente estabelecida.")
    else:
        print("❌ Falhas detectadas na integração Windows 11 Expandida.")

if __name__ == "__main__":
    main()
