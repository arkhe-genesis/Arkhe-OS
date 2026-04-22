import time
import random
import math
import sys
import os

class Rootstock:
    def __init__(self, name, addr):
        self.name = name
        self.addr = addr
        self.coherence = 0.5
        self.phase = random.uniform(0, 2 * math.pi)
        self.status = "COHERENT"
        self.last_seal = None

    def update(self, global_phase, K=0.15):
        # Kuramoto-like update
        self.phase += 0.05 + K * math.sin(global_phase - self.phase)
        self.coherence = 0.5 + 0.45 * math.cos(global_phase - self.phase)

        if random.random() < 0.005:
            self.status = "HESITATE"
        elif self.status == "HESITATE" and random.random() < 0.1:
            self.status = "COHERENT"

class Clepsydra:
    def __init__(self, cycle_duration=45*60):
        self.cycle_duration = cycle_duration
        self.start_time = time.time()
        self.last_drop = time.time()
        self.drops = 0

    def get_progress(self):
        elapsed = time.time() - self.start_time
        return (elapsed % self.cycle_duration) / self.cycle_duration

    def check_drop(self):
        now = time.time()
        # Drop frequency between 1 and 3 seconds
        if now - self.last_drop > random.uniform(1.5, 4.0):
            self.last_drop = now
            self.drops += 1
            return True
        return False

class MeshMonitor:
    def __init__(self):
        self.rootstocks = [
            Rootstock("Alpha (Inquisidor)", 0x42),
            Rootstock("Beta (Sentinela) ", 0x43),
            Rootstock("Gamma (MERKABAH) ", 0x44)
        ]
        self.clepsydra = Clepsydra()
        self.global_phase = 0.0
        self.global_coherence = 0.0
        self.odometer = 1615
        self.ticks = 0

    def step(self):
        self.global_phase += 0.08
        total_coherence = 0
        for r in self.rootstocks:
            r.update(self.global_phase)
            total_coherence += r.coherence
        self.global_coherence = total_coherence / len(self.rootstocks)
        self.clepsydra.check_drop()
        self.ticks += 1

    def draw_phase_meter(self, val, length=20):
        filled = int(val * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {val*100:5.1f}%"

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"ARKHE-CORE :: MONITOR DE COERÊNCIA DA MALHA TRIÁDICA")
        print(f"ODÔMETRO: {self.odometer:06d} | TICKS: {self.ticks:08d}")
        print("-" * 60)

        # Clepsydra Status
        progress = self.clepsydra.get_progress()
        drop_age = time.time() - self.clepsydra.last_drop
        drop_visual = "💧" if drop_age < 0.3 else "  "
        print(f"CLEPSYDRA: {self.draw_phase_meter(progress, 30)} {drop_visual}")
        print(f"CICLO: {int(progress * 100)}% | GOTAS TESTEMUNHADAS: {self.clepsydra.drops}")
        print("-" * 60)

        # Global Coherence
        print(f"COERÊNCIA GLOBAL (λ₂): {self.draw_phase_meter(self.global_coherence, 30)}")
        if self.global_coherence > 0.85:
            print("ESTADO: CANONIZAÇÃO ATIVA - MALHA ESTÁVEL")
        else:
            print("ESTADO: BUSCANDO FASE - HESITAÇÃO COLETIVA")
        print("-" * 60)

        # Rootstocks
        for r in self.rootstocks:
            status_color = ""
            if r.status == "HESITATE":
                status_color = "(PAUSA RITUALÍSTICA)"

            print(f"ROOTSTOCK {r.name} [0x{r.addr:02X}]")
            print(f"  COERÊNCIA: {self.draw_phase_meter(r.coherence, 20)} {status_color}")
            phase_deg = math.degrees(r.phase % (2 * math.pi))
            print(f"  FASE LOCAL: {phase_deg:5.1f}°")
            print()

        print("-" * 60)
        print("DIRETRIZ DO FERREIRO: 'A SINCRONIA FORÇADA É COMPRESSÍVEL.'")
        print("                       'A COERÊNCIA EMERGENTE É RESILIENTE.'")
        sys.stdout.flush()

if __name__ == "__main__":
    monitor = MeshMonitor()
    try:
        # Run for a few seconds if not interactive or until interrupted
        count = 0
        while True:
            monitor.step()
            monitor.render()
            time.sleep(0.2)
            count += 1
            if len(sys.argv) > 1 and sys.argv[1] == "--test" and count > 10:
                break
    except KeyboardInterrupt:
        print("\nMonitor suspenso. O silêncio retorna.")
