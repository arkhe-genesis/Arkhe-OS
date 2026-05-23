#!/usr/bin/env python3
"""
arkhe-codegraph — CodeGraph integration for ARKHE MegaKernel.
Provides CLI commands to init, index, and query CodeGraph from the ARKHE environment.
Arquiteto: ORCID 0009‑0005‑2697‑4668
"""

__version__ = "1.0.0"
__description__ = "CodeGraph semantic code knowledge graph for ARKHE agents"
__author__ = "ORCID 0009‑0005‑2697‑4668"

import subprocess, json, os
from pathlib import Path
import click

class CodeGraphBridge:
    """Bridge to the CodeGraph CLI."""

    def __init__(self):
        self.bin = os.environ.get("CODEGRAPH_BIN", "codegraph")

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run([self.bin] + list(args), capture_output=True, text=True)

    def init(self, path: str = "."):
        return self._run("init", path, "-i")

    def index(self, path: str = ".", force: bool = False):
        cmd = ["index", path]
        if force: cmd.append("--force")
        return self._run(*cmd)

    def status(self, path: str = "."):
        return self._run("status", path)

    def search(self, query: str, kind: str = None):
        cmd = ["query", query, "--json"]
        if kind: cmd.extend(["--kind", kind])
        return self._run(*cmd)

    def context(self, task: str, path: str = "."):
        return self._run("context", task, "--json")

    def callers(self, symbol: str, path: str = "."):
        return self._run("callers", symbol, "--json")

    def callees(self, symbol: str, path: str = "."):
        return self._run("callees", symbol, "--json")

    def affected(self, symbol: str, path: str = "."):
        return self._run("affected", symbol, "--json")

    def impact(self, symbol: str, depth: int = 3):
        return self._run("impact", symbol, "--depth", str(depth), "--json")

@click.group()
def codegraph():
    """CodeGraph semantic code knowledge graph."""
    pass

@codegraph.command("init")
@click.argument("path", default=".")
def cg_init(path: str):
    """Initialize CodeGraph in a project."""
    bridge = CodeGraphBridge()
    result = bridge.init(path)
    if result.returncode == 0:
        click.echo(f"✓ CodeGraph initialized in {path}")
    else:
        click.echo(f"[ERROR] {result.stderr}", err=True)

@codegraph.command("index")
@click.argument("path", default=".")
@click.option("--force", is_flag=True)
def cg_index(path: str, force: bool):
    """Build or rebuild the code knowledge graph."""
    bridge = CodeGraphBridge()
    result = bridge.index(path, force)
    click.echo(result.stdout or result.stderr)

@codegraph.command("status")
@click.argument("path", default=".")
def cg_status(path: str):
    """Show CodeGraph index statistics."""
    bridge = CodeGraphBridge()
    result = bridge.status(path)
    click.echo(result.stdout)

@codegraph.command("search")
@click.argument("query")
@click.option("--kind", help="Symbol kind (function, class, method, etc.)")
def cg_search(query: str, kind: str):
    """Search symbols in the code graph."""
    bridge = CodeGraphBridge()
    result = bridge.search(query, kind)
    if result.stdout:
        try:
            data = json.loads(result.stdout)
            for item in data[:10]:
                click.echo(f"  {item.get('name', item.get('symbol', str(item)))}")
        except json.JSONDecodeError:
            click.echo(result.stdout)
    else:
        click.echo("[No results]")

@codegraph.command("context")
@click.argument("task")
def cg_context(task: str):
    """Build AI context for a task."""
    bridge = CodeGraphBridge()
    result = bridge.context(task)
    click.echo(result.stdout[:2000])

@codegraph.command("callers")
@click.argument("symbol")
def cg_callers(symbol: str):
    """Trace what calls a function/method."""
    bridge = CodeGraphBridge()
    result = bridge.callers(symbol)
    click.echo(result.stdout)

@codegraph.command("callees")
@click.argument("symbol")
def cg_callees(symbol: str):
    """Trace what a function/method calls."""
    bridge = CodeGraphBridge()
    result = bridge.callees(symbol)
    click.echo(result.stdout)

@codegraph.command("affected")
@click.argument("symbol")
def cg_affected(symbol: str):
    """Analyze what code is affected by changing a symbol (alias for impact)."""
    bridge = CodeGraphBridge()
    result = bridge.affected(symbol)
    click.echo(result.stdout)

@codegraph.command("impact")
@click.argument("symbol")
@click.option("--depth", default=3, help="Max dependency traversal depth")
def cg_impact(symbol: str, depth: int):
    """Analyze impact radius of changing a symbol."""
    bridge = CodeGraphBridge()
    result = bridge.impact(symbol, depth)
    click.echo(result.stdout[:2000])

def register(cli: click.Group):
    cli.add_command(codegraph)
