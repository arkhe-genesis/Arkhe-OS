import os
import sys

def verify_controller():
    print("ARKHE(N) > VERIFICANDO BLOCO #419-Ω: CALIBRATION-CONTROLLER v1.4")
    controller_file = "src/arkhe_core/calibration_controller.py"
    if not os.path.exists(controller_file):
        print(f"[ERRO] Arquivo {controller_file} não encontrado.")
        return False

    with open(controller_file, "r") as f:
        content = f.read()
        if "ArkheCalibrationControllerV14" in content:
            print("[OK] Classe ArkheCalibrationControllerV14 verificada.")
        else:
            print("[ERRO] Classe ArkheCalibrationControllerV14 ausente.")
            return False

        if "NULL_BEFORE_NOISE" in content:
            print("[OK] Conceito Sagrado 'NULL_BEFORE_NOISE' verificado.")
        else:
            print("[ERRO] Conceito Sagrado 'NULL_BEFORE_NOISE' ausente.")
            return False

    return True

def verify_tool():
    tools_file = "src/tools/arkhe.ts"
    if not os.path.exists(tools_file):
        print(f"[ERRO] Arquivo {tools_file} não encontrado.")
        return False

    with open(tools_file, "r") as f:
        content = f.read()
        if "runV14Simulation" in content:
            print("[OK] MCP Tool runV14Simulation verificada.")
        else:
            print("[ERRO] MCP Tool runV14Simulation ausente.")
            return False
    return True

if __name__ == "__main__":
    if verify_controller() and verify_tool():
        print("\nARKHE(N) > BLOCO #419-Ω INTEGRADO COM SUCESSO.")
        sys.exit(0)
    else:
        print("\nARKHE(N) > FALHA NA VERIFICAÇÃO DO BLOCO #419-Ω.")
        sys.exit(1)
