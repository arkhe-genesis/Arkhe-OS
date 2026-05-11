import time
import os
import random
from datetime import datetime

# Cores ANSI
CIANO = '\033[96m'
VERDE = '\033[92m'
AMARELO = '\033[93m'
VERMELHO = '\033[91m'
RESET = '\033[0m'
NEGRITO = '\033[1m'

def display_dashboard():
    # Simula dados para o dashboard
    while True:
        os.system('clear')
        print(f"{NEGRITO}{CIANO}╔══════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{NEGRITO}{CIANO}║                CATEDRAL ARKHE(N) — VITRAL DE TEXTO (MTP 3.0)           ║{RESET}")
        print(f"{NEGRITO}{CIANO}╠══════════════════════════════════════════════════════════════════════════╣{RESET}")

        print(f"{CIANO}║ Gateway REST: {VERDE}ACTIVE{RESET} {CIANO}| Conexões: {random.randint(1,5)}{RESET}")
        print(f"{CIANO}║ Traduções: {random.randint(100,200)}{RESET}")

        print(f"{CIANO}╠══════════════════════════════════════════════════════════════════════════╣{RESET}")
        print(f"{NEGRITO}║ STATUS DOS PILARES (Containers){RESET}")
        pilares = ['cathedrald-core', 'quantum-bus', 'gateway', 'entropy-monitor', 'sapphire-node', 'diamond-node']
        for p in pilares:
            print(f"{CIANO}║   {p:<25s}: {VERDE}Up (healthy){RESET}")

        print(f"{CIANO}╠══════════════════════════════════════════════════════════════════════════╣{RESET}")
        print(f"{NEGRITO}║ MONITOR DE DISSIPAÇÃO ENTÓPICA{RESET}")
        ent = random.uniform(1.2, 1.8)
        print(f"{CIANO}║   Entropia Atual: {VERDE}{ent:.4f} bits{RESET}")
        print(f"{CIANO}║   Calor Acumulado: {random.uniform(0.1, 0.5):.4f} pJ{RESET}")
        print(f"{CIANO}║   Tempo de Coerência: {VERDE}inf s{RESET}")

        print(f"{NEGRITO}{CIANO}╚══════════════════════════════════════════════════════════════════════════╝{RESET}")
        print(f"{AMARELO}   Última atualização: {datetime.now().strftime('%H:%M:%S')} | CTRL+C para sair{RESET}")
        time.sleep(2)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\nSaindo do Vitral...")
