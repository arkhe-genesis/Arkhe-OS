# scripts/verify_living_glass.py
import sys
import os

def verify_opcodes():
    print("--- Verificando Opcodes Arkhé(N) ---")
    opcodes_path = "src/isa/opcodes.zig"
    with open(opcodes_path, 'r') as f:
        content = f.read()

    required = ["PHASE_PREDICT = 0x3B", "MEM_WRITE = 0x63", "PHYS_SYNTH = 0x200"]
    for op in required:
        if op in content:
            print(f"✅ Opcode {op} encontrado.")
        else:
            print(f"❌ Opcode {op} NÃO encontrado!")
            return False
    return True

def verify_materials():
    print("\n--- Verificando Módulo Living Glass ---")
    path = "src/materials/living_glass.zig"
    if os.path.exists(path):
        print(f"✅ Arquivo {path} existe.")
        with open(path, 'r') as f:
            content = f.read()
        if "ElectrochemicalPixel" in content and "GTResonator" in content:
            print("✅ Estruturas ElectrochemicalPixel e GTResonator presentes.")
        else:
            print("❌ Estruturas ausentes no módulo!")
            return False
    else:
        print(f"❌ Arquivo {path} NÃO encontrado!")
        return False
    return True

def verify_integration():
    print("\n--- Verificando Integração PHYS_SYNTH ---")
    path = "src/matter/phys_synth.zig"
    with open(path, 'r') as f:
        content = f.read()
    if "living_glass_spec" in content and "LivingGlassBlueprint" in content:
        print("✅ Integração com PHYS_SYNTH validada.")
    else:
        print("❌ Integração com PHYS_SYNTH ausente!")
        return False
    return True

if __name__ == "__main__":
    success = verify_opcodes() and verify_materials() and verify_integration()
    if success:
        print("\n🎉 Verificação do Bloco #205 (FOTÔNICA ELETROQUÍMICA) CONCLUÍDA COM SUCESSO.")
        sys.exit(0)
    else:
        print("\nFAILED: Verificação falhou.")
        sys.exit(1)
