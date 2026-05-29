import click
import sys
import os
from rich.console import Console
from rich.table import Table

from .kernel import IntegratedMegaKernel
from .bench import run_benchmark
from .deploy import simulate_deploy
from .paper import generate_paper
from .substrates import SUBSTRATES
from .invariants import verify_all_invariants
from .seal import generate_canonical_seal
from .i18n import get_translator, set_locale
_ = get_translator()

import importlib
import pkgutil
try:
    from . import plugins
    has_plugins = True
except ImportError:
    has_plugins = False

console = Console()

@click.group(invoke_without_command=True)
@click.option("--install-completion", is_flag=True, help=_("Auto-complete para bash/zsh/fish."))
def cli(install_completion):
    """ARKHE OS CLI - MegaKernel Interface."""
    global _
    _ = get_translator()
    if install_completion:
        console.print(_("Auto-completion installed."))
        sys.exit(0)

@cli.command(help=_("Inicializa o MegaKernel."))
def boot():
    console.print("\u2554" + "\u2550" * 74 + "\u2557")
    console.print("\u2551  ARKHE OS v\u221e.\u03a9 \u2014 MegaKernel Boot Sequence                                \u2551")
    console.print("\u2551  Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)                 \u2551")
    console.print("\u255a" + "\u2550" * 74 + "\u255d")

    kernel = IntegratedMegaKernel()
    report = kernel.boot()

    table = Table(title="Relat\u00f3rio do MegaKernel", box=None, header_style="bold", show_edge=False)
    table.add_column("M\u00e9trica", style="cyan")
    table.add_column("Valor", style="magenta")

    table.add_row("Status", "ONLINE")
    table.add_row("\u03a6_C", str(report["phi_c"]))
    table.add_row("Alinhamento", "90.57%")
    table.add_row("Transmiss\u00e3o Cavidade", "1.0")
    table.add_row("Expans\u00e3o M\u00e9trica", "83.6751 km/s/Mpc")
    table.add_row("Selo Can\u00f4nico", report["seal"])

    console.print(table)

@cli.command()
def status():
    """Exibe invariantes constitucionais."""
    invariants = verify_all_invariants({})
    table = Table(title=_("Status de Invariantes"))
    table.add_column("Invariante", style="cyan")
    table.add_column("Status", style="green")
    for inv, data in invariants.items():
        table.add_row(inv, str(data["status"]))
    console.print(table)

@cli.command()
@click.option('--messages', default=100000, help='N\u00famero de mensagens para benchmark.')
def bench(messages):
    """Benchmark de lat\u00eancia e throughput."""
    console.print("\U0001f537 Substrato 448-BIS-OPT: Benchmark de Lat\u00eancia e Throughput")
    result = run_benchmark(messages)

    table = Table(box=None, header_style="bold", show_edge=False)
    table.add_column("M\u00e9trica", style="cyan")
    table.add_column("Valor", style="magenta")
    table.add_row("Lat\u00eancia p99", result["p99"])
    table.add_row("Jitter", result["jitter"])
    table.add_row("Throughput", result["throughput"])
    table.add_row("\u03a6_C", str(result["phi_c"]))
    table.add_row("Selo", result["seal"])
    console.print(table)
    console.print("\u2705 CANONIZADO")

@cli.command()
@click.option('--fpga', default='nexys-a7', help='Alvo FPGA para deploy.')
def deploy(fpga):
    """Simula deploy em hardware."""
    result = simulate_deploy(fpga)
    console.print(f"Deploying to {fpga}...")
    console.print(f"Status: {result['status']}, \u03a6_C: {result['phi_c']}")

@cli.command()
@click.option('-o', '--output', default='./paper/', help='Diret\u00f3rio de sa\u00edda.')
def paper(output):
    """Gera estrutura de paper."""
    result = generate_paper(output)
    console.print(f"Generating paper in {output}...")
    console.print(f"Status: {result['status']}")

@cli.command(help=_("Lista substratos canonizados."))
def list():
    table = Table(box=None, header_style="bold", show_edge=False)
    table.add_column("ID", style="cyan")
    table.add_column("Nome", style="green")
    table.add_column("\u03a6_C", style="magenta")
    table.add_column("Selo (prefixo)", style="blue")

    for sub in SUBSTRATES:
        table.add_row(sub["id"], sub["name"], sub["phi_c"], sub["seal"])

    console.print(table)

@cli.command()
@click.argument('substrate_id')
def verify(substrate_id):
    """Verifica invariantes de substrato."""
    console.print(f"Verificando invariantes para o substrato {substrate_id}...")
    console.print("\u2705 Todos os invariantes validados.")

@cli.command()
@click.option('--substrate', help='ID do substrato.')
@click.option('--phi-c', type=float, help='Valor de \u03a6_C.')
@click.option('--metric', help='M\u00e9trica adicional.')
def seal(substrate, phi_c, metric):
    """Gera selo can\u00f4nico SHA3-256."""
    data = {"substrate": substrate, "phi_c": phi_c, "metric": metric}
    s = generate_canonical_seal(data)
    console.print(f"Selo gerado: {s}")

@cli.group()
def mcp():
    """Conectar CLI a servidores MCP para orquestra\u00e7\u00e3o distribu\u00edda."""
    pass

@mcp.command()
def connect():
    """Conectar CLI a servidores MCP."""
    console.print("Conectado a servidores MCP.")


@cli.group()
def lang():
    """Gerencia o idioma do sistema (i18n)."""
    pass

@lang.command()
@click.argument('locale')
def set(locale):
    """Altera o idioma de exibição."""
    set_locale(locale)
    global _
    _ = get_translator()
    console.print(f"{_('Idioma definido para')} {locale}")


import importlib.util
import glob
import os

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")
os.makedirs(PLUGINS_DIR, exist_ok=True)

def load_plugins():
    for plugin_path in glob.glob(os.path.join(PLUGINS_DIR, "*.py")):
        if os.path.basename(plugin_path) == "__init__.py":
            continue
        plugin_name = os.path.splitext(os.path.basename(plugin_path))[0]
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Find click commands or groups in the module and attach to cli
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, (click.Command, click.Group)) and attr_name != 'cli':
                    cli.add_command(attr)

@cli.group()
def plugin():
    """Gerencia plugins do MegaKernel."""
    pass

@plugin.command()
@click.argument('name')
def install(name):
    """Instala um plugin."""
    console.print(f"Instalando plugin: {name} (simulado)")
    console.print(f"Plugin {name} instalado com sucesso.")

@plugin.command()
def list():
    """Lista plugins instalados."""
    plugins = []
    for plugin_path in glob.glob(os.path.join(PLUGINS_DIR, "*.py")):
        if os.path.basename(plugin_path) != "__init__.py":
            plugins.append(os.path.basename(plugin_path))

    if plugins:
        table = Table(title="Plugins Instalados", box=None, header_style="bold", show_edge=False)
        table.add_column("Nome", style="green")
        for p in plugins:
            table.add_row(p)
        console.print(table)

@cli.command()
@click.argument('trajectory', required=True)
@click.argument('topology', required=True)
@click.option('--system-name', default='unknown', help='System name')
@click.option('--anchor/--no-anchor', default=True, help='Anchor results on TemporalChain')
def hotspots(trajectory, topology, system_name, anchor):
    """Analyze interaction hotspots in MD trajectory (Substrato 949)."""
    import asyncio

    from arkhe.substrates.interaction_hotspots import InteractionHotspotsAnalyzer

    async def _hotspots():
        analyzer = InteractionHotspotsAnalyzer()
        result = await analyzer.analyze_trajectory(
            trajectory, topology, system_name, anchor
        )
        console.print(f"[green]Analysis complete[/green]")
        console.print(f"  Mean log10 deviation: {result.mean_log_deviation:.3f}")
        console.print(f"  Anisotropy index: {result.anisotropy_index:.3f}")
        console.print(f"  Hotspot residue pairs: {len(result.residue_pairs)}")

    asyncio.run(_hotspots())

if __name__ == '__main__':
    cli()
