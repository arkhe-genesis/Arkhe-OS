import time
import os
import random
import math
import sys

# Simulation State
odometer = 1632
ghz_quality = 0.947
global_coherence = 0.58
last_collapse_time = 1629.007
last_collapse_verdict = "DENY"

nodes = {
    "alpha": {"phase": 2.31, "drift": 0.01, "coherence": 0.92},
    "beta":  {"phase": 2.31, "drift": 0.012, "coherence": 0.93},
    "gamma": {"phase": 2.31, "drift": 0.009, "coherence": 0.91},
    "delta": {"phase": 2.31, "drift": 0.015, "coherence": 0.87}
}

edges = {
    "alpha-beta": 0.92, "alpha-gamma": 0.91, "alpha-delta": 0.87,
    "beta-gamma": 0.93, "beta-delta": 0.86, "gamma-delta": 0.88
}

verdicts = [
    {"time": 1629.007, "node": "alpha", "verdict": "DENY", "prob": 0.947, "seal": "a1b2c3"},
    {"time": 1628.994, "node": "gamma", "verdict": "ALLOW", "prob": 0.912, "seal": "c3d4e5"},
    {"time": 1628.981, "node": "beta", "verdict": "DENY", "prob": 0.891, "seal": "e5f6g7"},
    {"time": 1628.955, "node": "alpha", "verdict": "DENY", "prob": 0.934, "seal": "7890ab"}
]

mode = "status"

def render_orb(phase):
    chars = ["-", "\\", "|", "/"]
    idx = int((phase / (2 * math.pi)) * 4) % 4
    return f"[{chars[idx]}]"

def draw_bar(val, length=20, char="▓", empty="░"):
    filled = int(val * length)
    return char * filled + empty * (length - filled)

def clear_screen():
    print("\033[2J\033[H", end="")

def render_dashboard():
    clear_screen()
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  K6O QUANTUM MESH — ESPELHO SILENCIOSO v4.0                                │")
    print(f"│  Clepsydra: {odometer:06d} gotas | Protocolo: quantum://GHZ4                        │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print("│                                                                             │")
    print("│  [PAINEL 1: TOPOLOGIA TETRAÉDRICA]        [PAINEL 2: COERÊNCIA GLOBAL]      │")
    print("│                                                                             │")
    print(f"│         α({nodes['alpha']['phase']:.2f})                                                             │")
    print("│        /│\\              r₄(t) = " + f"{global_coherence:.2f}" + "                                          │")
    print(f"│       / │ \\             {draw_bar(global_coherence, 20)} {int(global_coherence*100)}%                              │")
    print(f"│      /  │  \\            [{draw_bar(global_coherence, 20, '█')}]  Resiliência                    │")
    print(f"│   β({nodes['beta']['phase']:.2f})─γ({nodes['gamma']['phase']:.2f})       Fidelidade: {ghz_quality:.3f}                                   │")
    print(f"│      \\  │  /            Último colapso: {last_collapse_time:08.3f} ({last_collapse_verdict})                     │")
    print("│       \\ │ /                                                                 │")
    print("│        \\│/                                                                  │")
    print(f"│         δ({nodes['delta']['phase']:.2f})                                                             │")
    print("│                                                                             │")
    print("│  [PAINEL 3: QUALIDADE DE EMARANHAMENTO]   [PAINEL 4: ÚLTIMOS JULGAMENTOS]   │")
    print("│                                                                             │")
    print(f"│  α─β: {draw_bar(edges['alpha-beta'], 10, '█')} {edges['alpha-beta']:.2f}     α─γ: {draw_bar(edges['alpha-gamma'], 10, '█')} {edges['alpha-gamma']:.2f}    α─δ: {draw_bar(edges['alpha-delta'], 10, '█')} {edges['alpha-delta']:.2f}      │")
    print(f"│  β─γ: {draw_bar(edges['beta-gamma'], 10, '█')} {edges['beta-gamma']:.2f}     β─δ: {draw_bar(edges['beta-delta'], 10, '█')} {edges['beta-delta']:.2f}    γ─δ: {draw_bar(edges['gamma-delta'], 10, '█')} {edges['gamma-delta']:.2f}      │")
    print("│                                                                             │")
    base_tri = (edges["alpha-beta"] + edges["alpha-gamma"] + edges["beta-gamma"]) / 3
    delta_edges = (edges["alpha-delta"] + edges["beta-delta"] + edges["gamma-delta"]) / 3
    print(f"│  Triângulo base (αβγ): {base_tri:.2f}    Arestas para δ: {delta_edges:.2f}                         │")
    min_edge = min(edges.values())
    min_name = [k for k, v in edges.items() if v == min_edge][0]
    warn = "SIM ⚠" if min_edge < 0.85 else "NÃO ✓"
    print(f"│  Risco de fissura: {min_name} ({min_edge:.2f}) < limiar 0.85? {warn}                              │")
    print("│                                                                             │")
    print("│  ┌──────────┬────────┬────────┬────────────────────────┬──────────┐          │")
    print("│  │ Timestamp│ Node   │ Verdict│ Prob Pré-Colapso       │ Selo     │          │")
    print("│  ├──────────┼────────┼────────┼────────────────────────┼──────────┤          │")
    for v in verdicts:
        print(f"│  │{v['time']:010.3f}│   {v['node']:<5}│  {v['verdict']:<5}│ {v['prob']:.3f}                  │ {v['seal']}... │          │")
    print("│  └──────────┴────────┴────────┴────────────────────────┴──────────┘          │")
    print("│                                                                             │")
    print("│  [LINHA DE COMANDO RITUAL]                                                  │")
    print("│  arkhe > _                                                                  │")
    print("│                                                                             │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")

def render_spin():
    clear_screen()
    print("┌─────────────────────────────────────────────────────────┐")
    print("│  MODO SPIN — Visualização de Qubits Individuais         │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│                                                         │")
    for name, data in nodes.items():
        p0 = 0.5 + 0.25 * math.sin(data['phase']) # Simulado
        p1 = 1.0 - p0
        print(f"│  {name}: |ψ⟩ = {math.sqrt(p0):.2f}|0⟩ + {math.sqrt(p1):.2f}|1⟩  [Bloch: θ={math.acos(2*p0-1):.2f} φ={data['phase']:.2f}]   │")
        print(f"│      {draw_bar(p0, 15, '█')}  P(|0⟩)={p0:.2f}  P(|1⟩)={p1:.2f}          │")
        print("│                                                         │")
    print("└─────────────────────────────────────────────────────────┘")

def render_ripple():
    clear_screen()
    print("┌─────────────────────────────────────────────────────────┐")
    print("│  MODO ONDULAÇÃO — Histórico de Fases                    │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│                                                         │")
    for name, data in nodes.items():
        wave = ""
        for i in range(20):
            val = math.sin(data['phase'] + i * 0.5)
            if val > 0.5: wave += "╱"
            elif val < -0.5: wave += "╲"
            else: wave += "─"
        print(f"│  {name}: {wave}  [σ={data['drift']:.2f} rad]         │")
    print("│                                                         │")
    print("└─────────────────────────────────────────────────────────┘")

def render_codex():
    clear_screen()
    print("┌─────────────────────────────────────────────────────────┐")
    print("│  MODO CÓDICE — Últimas Entradas do Códice Quântico      │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│                                                         │")
    print(f"│  [{odometer}.001] GHZ4_FUSION: δ iniciado com sucesso      │")
    print(f"│               Coerência pós-fusão: {global_coherence:.2f}                  │")
    print("│                                                         │")
    for v in verdicts:
        print(f"│  [{v['time']:.3f}] QUANTUM_VERDICT: {v['verdict']}                     │")
        print(f"│               Payload: {v['seal']}... Juiz: {v['node']}            │")
    print("│                                                         │")
    print("└─────────────────────────────────────────────────────────┘")

def handle_input(cmd):
    global mode, odometer, global_coherence
    cmd = cmd.lower().strip()
    if cmd == "status": mode = "status"
    elif cmd.startswith("spin"): mode = "spin"
    elif cmd == "ripple": mode = "ripple"
    elif cmd == "codex": mode = "codex"
    elif cmd == "sync":
        print("[SYNC] Iniciando sincronização GHZ₄...")
        time.sleep(0.5)
        global_coherence = min(0.99, global_coherence + 0.05)
        odometer += 1
    elif cmd == "quit": sys.exit(0)
    else: print(f"Comando desconhecido: {cmd}")

if __name__ == "__main__":
    # If interactive (has tty)
    if sys.stdin.isatty() and len(sys.argv) == 1:
        try:
            while True:
                if mode == "status": render_dashboard()
                elif mode == "spin": render_spin()
                elif mode == "ripple": render_ripple()
                elif mode == "codex": render_codex()

                user_input = input("arkhe > ")
                handle_input(user_input)
        except KeyboardInterrupt:
            print("\nMonitor suspenso.")
    else:
        # Non-interactive mode for testing
        render_dashboard()
        print("\n[Non-interactive test complete]")
