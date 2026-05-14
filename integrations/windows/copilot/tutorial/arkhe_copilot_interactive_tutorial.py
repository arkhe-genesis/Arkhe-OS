import argparse
import sys
import time

def print_slow(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def generate_circuit():
    print_slow("\n>> 'Copilot, crie um circuito quântico com 3 qubits, aplique H no primeiro, CNOT entre 1 e 2, e depois X no terceiro'")
    print_slow("\nCopilot (usando Arkhe):")
    print_slow("✅ Circuito gerado:")
    code = '''```python
from arkhe.qpu import QuantumCircuit, PulseSequencer

qc = QuantumCircuit(3)
qc.h(0)
qc.cnot(1, 2)
qc.x(2)

seq = PulseSequencer('arkhe_pulse_sequencer.bit')
result = seq.execute(qc, drag_alpha=0.15)
print('Φ_C after circuit:', result.phi_c)
```'''
    print(code)
    print_slow("Circuito ancorado na TemporalChain (selo: a3f2b8c9...). Deseja executar agora?")

def analyze_phi_c():
    print_slow("\n>> 'Qual é o Φ_C atual do sistema?'")
    print_slow("\nCopilot:")
    print_slow("Φ_C atual: 0.9987 (Excelente)")
    print_slow("Tendência recente: 0.9975 → 0.9982 → 0.9987")
    print_slow("Nós online: 4")

def deploy_intune():
    print_slow("\n>> 'Implante a última versão do Arkhe Runtime para os dispositivos do grupo \"workstations\" via Intune.'")
    print_slow("\nCopilot:")
    print_slow("✅ Deploy iniciado via Intune para o grupo 'workstations'. ID do deployment: 550e8400-e29b-41d4-a716-446655440000")
    print_slow("Progresso: 15% (22/150 dispositivos)")

def main():
    parser = argparse.ArgumentParser(description="Arkhe Copilot Interactive Tutorial")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode for tests")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ARKHE Ω-TEMP v7.6.1 — COPILOT-ASSISTED DEVELOPMENT          ║")
    print("║  Tutorial Interativo                                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    if args.non_interactive:
        # Just run through the steps without waiting for input and with fast printing
        global print_slow
        def print_slow(text, delay=0):
            print(text)

        generate_circuit()
        analyze_phi_c()
        deploy_intune()
        print("\n[Modo Não-Interativo] Tutorial concluído.")
        return

    print_slow("Bem-vindo ao tutorial interativo do Arkhe Copilot.")
    print_slow("Neste tutorial, você aprenderá a interagir com o assistente de IA da Catedral.")

    while True:
        print("\nSelecione uma ação:")
        print("1. Gerar Circuito Quântico")
        print("2. Analisar Coerência Φ_C")
        print("3. Deploy via Intune")
        print("4. Sair")

        try:
            choice = input("\nEscolha (1-4): ")
        except EOFError:
            break

        if choice == '1':
            generate_circuit()
        elif choice == '2':
            analyze_phi_c()
        elif choice == '3':
            deploy_intune()
        elif choice == '4':
            print_slow("Encerrando tutorial. Que a coerência esteja com você.")
            break
        else:
            print("Escolha inválida.")

if __name__ == "__main__":
    main()
