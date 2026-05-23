#!/usr/bin/env python3
"""
ARKHE OS — Plugin CodeGraph Bridge
Arquiteto: ORCID 0009-0005-2697-4668
Data: 2026-05-23
STRICT MODE

Integra CodeGraph (colbymchenry/codegraph) ao MegaKernel ARKHE.
Pre-indexed semantic code knowledge graph com cache de duas camadas:
Estrutural (CodeGraph) + Semântica (PEEK 610).
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

console = Console()

# Diretório de cache CodeGraph
CODEGRAPH_DIR = Path.home() / ".arkhe" / "codegraph"
CODEGRAPH_DIR.mkdir(parents=True, exist_ok=True)


class CodeGraphBridge:
    """Bridge to the CodeGraph CLI (npx @colbymchenry/codegraph)."""

    def __init__(self, binary: str = "npx @colbymchenry/codegraph"):
        self.binary = binary
        self.version = "1.0.0"

    def _run(self, *args, cwd: Optional[str] = None, timeout: int = 300) -> Dict:
        """Executa comando CodeGraph e retorna resultado estruturado."""
        cmd = self.binary.split() + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or os.getcwd(),
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Timeout", "returncode": -1}
        except FileNotFoundError:
            return {"success": False, "stdout": "", "stderr": "CodeGraph not found: {}".format(self.binary), "returncode": -1}

    def is_installed(self) -> bool:
        """Verifica se CodeGraph está instalado."""
        result = self._run("--version", timeout=10)
        return result["success"]

    def init(self, path: str = ".", interactive: bool = False) -> Dict:
        """Inicializa CodeGraph em um repositório."""
        args = ["init", path]
        if interactive:
            args.append("-i")
        return self._run(*args)

    def index(self, path: str = ".", force: bool = False) -> Dict:
        """Indexa ou re-indexa o grafo de código."""
        args = ["index", path]
        if force:
            args.append("--force")
        return self._run(*args)

    def status(self, path: str = ".") -> Dict:
        """Mostra estatísticas do índice."""
        return self._run("status", path)

    def search(self, query: str, kind: Optional[str] = None,
               limit: int = 20) -> List[Dict]:
        """Busca símbolos no grafo via FTS5."""
        args = ["search", query, "--json", "-l", str(limit)]
        if kind:
            args.extend(["--kind", kind])
        result = self._run(*args)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return []

    def context(self, task: str, path: str = ".") -> Dict:
        """Constrói contexto para uma tarefa."""
        result = self._run("context", task, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def callers(self, symbol: str, path: str = ".") -> List[Dict]:
        """Trace callers de um símbolo (quem chama)."""
        result = self._run("callers", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return []

    def callees(self, symbol: str, path: str = ".") -> List[Dict]:
        """Trace callees de um símbolo (quem é chamado)."""
        result = self._run("callees", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return []

    def impact(self, symbol: str, depth: int = 3, path: str = ".") -> Dict:
        """Analisa impacto de alterar um símbolo."""
        result = self._run("impact", symbol, "--depth", str(depth), "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def explore(self, files: List[str], path: str = ".") -> Dict:
        """Explora arquivos específicos no grafo."""
        args = ["explore"] + files + ["--json"]
        result = self._run(*args, cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def node(self, symbol: str, path: str = ".") -> Dict:
        """Retorna detalhes de um nó específico."""
        result = self._run("node", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}


# ============================================================
# INTEGRAÇÃO 611↔610 — CODEGRAPH + PEEK (CACHE DE DUAS CAMADAS)
# ============================================================

class CodeGraphPEEKIntegration:
    """
    Cache de duas camadas: Estrutural (CodeGraph) + Semântica (PEEK).

    CodeGraph fornece o índice estrutural do código (AST, symbols, edges).
    PEEK (610) cacheia a orientação semântica acumulada em sessões anteriores.
    """

    def __init__(self, codegraph: CodeGraphBridge, peek_manager=None):
        self.cg = codegraph
        self.peek = peek_manager  # Referência ao PEEKManager do plugin 610
        self.cache_dir = CODEGRAPH_DIR / "peek_integration"
        self.cache_dir.mkdir(exist_ok=True)

    def query_with_cache(self, repo_path: str, query: str,
                         task_type: str = "general") -> Dict:
        """
        Query híbrida: primeiro consulta PEEK (cache semântico),
        depois CodeGraph (índice estrutural), combina resultados.
        """
        results = {
            "query": query,
            "task_type": task_type,
            "peek_results": [],
            "codegraph_results": [],
            "combined": [],
            "source": "hybrid",
        }

        # Camada 1: PEEK (cache semântico)
        if self.peek:
            peek_map_id = "codegraph-{}".format(Path(repo_path).name)
            peek_results = self.peek.query_map(peek_map_id, query)
            results["peek_results"] = peek_results

        # Camada 2: CodeGraph (índice estrutural)
        cg_results = self.cg.search(query, limit=20)
        results["codegraph_results"] = cg_results

        # Combinar: priorizar PEEK (mais relevante semanticamente)
        combined = []
        seen = set()

        # Adicionar resultados PEEK primeiro
        for pr in results["peek_results"]:
            key = pr.get("content", "")[:50]
            if key not in seen:
                combined.append({
                    "source": "peek",
                    "section": pr.get("section", ""),
                    "content": pr.get("content", ""),
                    "priority": pr.get("priority", 0),
                })
                seen.add(key)

        # Adicionar resultados CodeGraph
        for cr in results["codegraph_results"]:
            key = cr.get("name", "") + cr.get("kind", "")
            if key not in seen:
                combined.append({
                    "source": "codegraph",
                    "name": cr.get("name", ""),
                    "kind": cr.get("kind", ""),
                    "file": cr.get("file", ""),
                    "line": cr.get("line", 0),
                })
                seen.add(key)

        results["combined"] = combined
        return results

    def cache_exploration(self, repo_path: str, query: str,
                          exploration_result: Dict):
        """Cacheia resultado de exploração no PEEK para sessões futuras."""
        if not self.peek:
            return

        peek_map_id = "codegraph-{}".format(Path(repo_path).name)

        # Criar trajectory sintética a partir do resultado
        trajectory = [{
            "turn_id": 0,
            "observation": "Exploring {} for {}".format(repo_path, query),
            "action": "CodeGraph search: {}".format(query),
            "result": json.dumps(exploration_result, default=str)[:1000],
        }]

        # Atualizar PEEK
        if peek_map_id not in self.peek.maps:
            self.peek.create_map(
                map_id=peek_map_id,
                name="CodeGraph Cache: {}".format(Path(repo_path).name),
                source=repo_path,
                budget=2048,
            )

        self.peek.update_map(peek_map_id, trajectory)


# ============================================================
# COMANDOS CLICK
# ============================================================

def register_commands() -> Dict[str, click.Command]:

    @click.command(name="codegraph")
    @click.option("--version", "show_version", is_flag=True)
    @click.option("--install", "install_codegraph", is_flag=True)
    @click.option("--status", "show_status", is_flag=True)
    def codegraph_cmd(show_version, install_codegraph, show_status):
        """CodeGraph — Pre-indexed Code Knowledge Graph (colbymchenry)."""
        bridge = CodeGraphBridge()

        if install_codegraph:
            console.print("[bold blue]Installing CodeGraph:[/bold blue]")
            console.print("[dim]npm install -g @colbymchenry/codegraph[/dim]")
            console.print("[dim]Or: npx @colbymchenry/codegraph --version[/dim]")
            return

        if show_version or not bridge.is_installed():
            status = "[green]installed[/green]" if bridge.is_installed() else "[red]not installed[/red]"
            panel = Panel.fit(
                "[bold]CodeGraph (colbymchenry)[/bold]\n"
                "Version: {}\n"
                "Status: {}\n"
                "Languages: 19+\n"
                "Frameworks: 14+\n"
                "Repository: https://github.com/colbymchenry/codegraph\n"
                "Cache: {}".format(bridge.version, status, CODEGRAPH_DIR),
                title="ψ", border_style="bright_blue",
            )
            console.print(panel)
            return

        if show_status:
            result = bridge.status()
            if result["success"]:
                console.print(result["stdout"])
            else:
                console.print("[red]{}[/red]".format(result['stderr']))
            return

    @click.command(name="cg-init")
    @click.argument("path", default=".")
    @click.option("--interactive", "-i", is_flag=True, help="Interactive setup")
    def cg_init(path, interactive):
        """Initialize CodeGraph in a repository."""
        bridge = CodeGraphBridge()
        result = bridge.init(path, interactive)
        if result["success"]:
            console.print("[green]✓ CodeGraph initialized in {}[/green]".format(path))
            if result["stdout"]:
                console.print(result["stdout"])
        else:
            console.print("[red]✗ Error: {}[/red]".format(result['stderr']))

    @click.command(name="cg-index")
    @click.argument("path", default=".")
    @click.option("--force", is_flag=True, help="Force rebuild")
    def cg_index(path, force):
        """Build or rebuild the code knowledge graph."""
        bridge = CodeGraphBridge()
        console.print("[bold blue]Indexing {}...[/bold blue]".format(path))
        result = bridge.index(path, force)
        if result["success"]:
            console.print("[green]✓ Index complete[/green]")
            if result["stdout"]:
                console.print(result["stdout"][:2000])
        else:
            console.print("[red]✗ Error: {}[/red]".format(result['stderr']))

    @click.command(name="cg-search")
    @click.argument("query")
    @click.option("--kind", help="Symbol kind filter")
    @click.option("--limit", "-l", default=20, help="Max results")
    def cg_search(query, kind, limit):
        """Search symbols in the code graph."""
        bridge = CodeGraphBridge()
        results = bridge.search(query, kind, limit)

        if not results:
            console.print("[yellow]No results for '{}'[/yellow]".format(query))
            return

        table = Table(title="CodeGraph Search: '{}'".format(query))
        table.add_column("Name", style="cyan")
        table.add_column("Kind", style="green")
        table.add_column("File", style="white")
        table.add_column("Line", style="yellow")

        for r in results:
            table.add_row(
                r.get("name", "N/A"),
                r.get("kind", "N/A"),
                r.get("file", "N/A")[-40:] if r.get("file") else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-callers")
    @click.argument("symbol")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_callers(symbol, path):
        """Find all callers of a symbol (who calls it)."""
        bridge = CodeGraphBridge()
        results = bridge.callers(symbol, path)

        if not results:
            console.print("[yellow]No callers found for '{}'[/yellow]".format(symbol))
            return

        table = Table(title="Callers of '{}'".format(symbol))
        table.add_column("Caller", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Line", style="yellow")

        for r in results:
            table.add_row(
                r.get("name", "N/A"),
                r.get("file", "N/A")[-40:] if r.get("file") else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-callees")
    @click.argument("symbol")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_callees(symbol, path):
        """Find all callees of a symbol (what it calls)."""
        bridge = CodeGraphBridge()
        results = bridge.callees(symbol, path)

        if not results:
            console.print("[yellow]No callees found for '{}'[/yellow]".format(symbol))
            return

        table = Table(title="Callees of '{}'".format(symbol))
        table.add_column("Callee", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Line", style="yellow")

        for r in results:
            table.add_row(
                r.get("name", "N/A"),
                r.get("file", "N/A")[-40:] if r.get("file") else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-impact")
    @click.argument("symbol")
    @click.option("--depth", "-d", default=3, help="Max traversal depth")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_impact(symbol, depth, path):
        """Analyze impact radius of changing a symbol."""
        bridge = CodeGraphBridge()
        result = bridge.impact(symbol, depth, path)

        if not result:
            console.print("[yellow]No impact data for '{}'[/yellow]".format(symbol))
            return

        tree = Tree("[bold]Impact Analysis: {}[/bold] (depth={})".format(symbol, depth))

        if "affected" in result:
            affected = result["affected"]
            aff_tree = tree.add("[red]Affected ({})[/red]".format(len(affected)))
            for item in affected[:20]:
                aff_tree.add("[cyan]{}[/cyan] [{}]".format(item.get('name', 'N/A'), item.get('kind', 'N/A')))

        if "callers" in result:
            callers = result["callers"]
            call_tree = tree.add("[yellow]Callers ({})[/yellow]".format(len(callers)))
            for item in callers[:10]:
                call_tree.add(item.get("name", "N/A"))

        if "callees" in result:
            callees = result["callees"]
            cal_tree = tree.add("[green]Callees ({})[/green]".format(len(callees)))
            for item in callees[:10]:
                cal_tree.add(item.get("name", "N/A"))

        console.print(tree)

    @click.command(name="cg-affected")
    @click.argument("symbol")
    @click.option("--depth", "-d", default=3, help="Max traversal depth")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_affected(symbol, depth, path):
        """Security audit: list all symbols affected by changing a target (alias for cg-impact)."""
        # Delega para cg-impact com formatação específica para auditoria
        bridge = CodeGraphBridge()
        result = bridge.impact(symbol, depth, path)

        if not result:
            console.print("[red]✗ No data for '{}'[/red]".format(symbol))
            return

        affected = result.get("affected", [])
        console.print("[bold]Security Audit: Affected by '{}'[/bold]".format(symbol))
        console.print("[dim]Depth: {} | Total affected: {}[/dim]".format(depth, len(affected)))

        if affected:
            table = Table(title="Affected Symbols")
            table.add_column("Symbol", style="cyan")
            table.add_column("Kind", style="green")
            table.add_column("File", style="white")
            table.add_column("Severity", style="red")

            for item in affected:
                kind = item.get("kind", "unknown")
                severity = "HIGH" if kind in ["function", "method", "class"] else "MEDIUM"
                table.add_row(
                    item.get("name", "N/A"),
                    kind,
                    item.get("file", "N/A")[-30:] if item.get("file") else "N/A",
                    severity,
                )
            console.print(table)
        else:
            console.print("[green]✓ No affected symbols found[/green]")

    @click.command(name="cg-peek")
    @click.argument("query")
    @click.option("--repo", "-r", default=".", help="Repository path")
    @click.option("--task", "-t", default="general", help="Task type")
    def cg_peek(query, repo, task):
        """Hybrid query: CodeGraph (structural) + PEEK (semantic cache)."""
        console.print("[bold blue]Hybrid Query (CodeGraph + PEEK): '{}'[/bold blue]".format(query))
        console.print("[dim]Repository: {} | Task: {}[/dim]".format(repo, task))

        # Verificar se PEEK está disponível
        try:
            from arkhe.plugins.peek.peek_bridge import PEEKManager
            peek = PEEKManager()
            has_peek = True
        except ImportError:
            peek = None
            has_peek = False

        bridge = CodeGraphBridge()
        integration = CodeGraphPEEKIntegration(bridge, peek)

        results = integration.query_with_cache(repo, query, task)

        console.print("\n[green]✓ Results: {}[/green]".format(len(results['combined'])))
        console.print("[dim]  PEEK: {} | CodeGraph: {}[/dim]".format(len(results['peek_results']), len(results['codegraph_results'])))

        if results["combined"]:
            table = Table(title="Hybrid Results")
            table.add_column("Source", style="yellow")
            table.add_column("Name/Content", style="cyan")
            table.add_column("Meta", style="green")

            for item in results["combined"][:20]:
                if item["source"] == "peek":
                    table.add_row("PEEK", item["content"][:50], "p={:.2f}".format(item['priority']))
                else:
                    table.add_row("CodeGraph", item["name"], "{}:{}".format(item['kind'], item['line']))

            console.print(table)

        # Cacheiar resultado
        if has_peek:
            integration.cache_exploration(repo, query, results)
            console.print("\n[dim]✓ Cached in PEEK for future sessions[/dim]")

    return {
        "codegraph": codegraph_cmd,
        "cg-init": cg_init,
        "cg-index": cg_index,
        "cg-search": cg_search,
        "cg-callers": cg_callers,
        "cg-callees": cg_callees,
        "cg-impact": cg_impact,
        "cg-affected": cg_affected,
        "cg-peek": cg_peek,
    }
