# monitor_hud.py
import time
import threading
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class FerreiroHUD:
    def __init__(self, agent_ref):
        self.agent = agent_ref
        self.latencies = []
        self.layout = Layout()
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )

    def _build_header(self):
        return Panel(
            Text("TAU v1.2 — MONITOR DO FERREIRO", justify="center", style="bold white on blue"),
            style="blue"
        )

    def _build_body(self):
        table = Table(expand=True, show_header=True, header_style="bold magenta")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="green")

        # Calcula throughput
        now = time.time()
        tps = len([t for t in self.latencies if now - t < 1.0])
        avg_lat = (sum(self.latencies[-50:]) / len(self.latencies[-50:])) * 1000 if self.latencies else 0.0

        table.add_row("Frames Processados", f"{self.agent.frame_count}")
        table.add_row("Throughput (tokens/s)", f"{tps}")
        table.add_row("Latência Firebase (ms)", f"{avg_lat:.2f}")
        table.add_row("Read Pointer (Ring Buf)", f"0x{self.agent.read_ptr:08X}")
        table.add_row("Status UIO/IRQ", "[bold green]OK" if self.agent.uio_fd else "[bold red]DOWN")

        return Panel(table, title="Pipeline RHO -> Firebase", border_style="green")

    def _build_footer(self):
        status = "[bold green]AWAITING FIRST PHOTON" if self.agent.frame_count == 0 else "[bold yellow]PROCESSING"
        return Panel(Text(status, justify="center"), style="white on black")

    def update(self):
        self.layout["header"].update(self._build_header())
        self.layout["body"].update(self._build_body())
        self.layout["footer"].update(self._build_footer())
        return self.layout
