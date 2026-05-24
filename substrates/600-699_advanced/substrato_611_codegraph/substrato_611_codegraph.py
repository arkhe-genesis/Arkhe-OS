import json
import os
import tempfile

class Substrate611CodeGraph:
    def __init__(self):
        self.init_py = r"""\"\"\"ARKHE OS — Plugin codegraph (CodeGraph Knowledge Graph)\"\"\"
from .codegraph_bridge import register_commands
__all__ = ["register_commands"]
"""
        self.plugin_toml = r"""[plugin]
name = "codegraph"
version = "1.0.0"
description = "CodeGraph — Pre-indexed Code Knowledge Graph for AI Agents (colbymchenry)"
author = "ORCID 0009-0005-2697-4668"
license = "MIT"
entry_point = "codegraph_bridge"
dependencies = ["click", "rich", "subprocess"]
arkhe_version = "∞.Ω.∇+++"
"""
        self.codegraph_bridge_py = r"""#!/usr/bin/env python3
\"\"\"
ARKHE OS — Plugin CodeGraph Bridge
Arquiteto: ORCID 0009-0005-2697-4668
STRICT MODE

Integra CodeGraph (colbymchenry/codegraph) ao MegaKernel ARKHE.
Pre-indexed semantic code knowledge graph com cache de duas camadas:
Estrutural (CodeGraph) + Semantica (PEEK 610).
\"\"\"

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

CODEGRAPH_DIR = Path.home() / ".arkhe" / "codegraph"
CODEGRAPH_DIR.mkdir(parents=True, exist_ok=True)

class CodeGraphBridge:
    def __init__(self, binary: str = "npx @colbymchenry/codegraph"):
        self.binary = binary
        self.version = "1.0.0"

    def _run(self, *args, cwd: Optional[str] = None, timeout: int = 300) -> Dict:
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
            return {"success": False, "stdout": "", "stderr": "CodeGraph not found: " + self.binary, "returncode": -1}

    def is_installed(self) -> bool:
        result = self._run("--version", timeout=10)
        return result["success"]

    def init(self, path: str = ".", interactive: bool = False) -> Dict:
        args = ["init", path]
        if interactive:
            args.append("-i")
        return self._run(*args)

    def index(self, path: str = ".", force: bool = False) -> Dict:
        args = ["index", path]
        if force:
            args.append("--force")
        return self._run(*args)

    def status(self, path: str = ".") -> Dict:
        return self._run("status", path)

    def search(self, query: str, kind: Optional[str] = None, limit: int = 20) -> List[Dict]:
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
        result = self._run("context", task, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def callers(self, symbol: str, path: str = ".") -> List[Dict]:
        result = self._run("callers", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return []

    def callees(self, symbol: str, path: str = ".") -> List[Dict]:
        result = self._run("callees", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return []

    def impact(self, symbol: str, depth: int = 3, path: str = ".") -> Dict:
        result = self._run("impact", symbol, "--depth", str(depth), "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def explore(self, files: List[str], path: str = ".") -> Dict:
        args = ["explore"] + files + ["--json"]
        result = self._run(*args, cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

    def node(self, symbol: str, path: str = ".") -> Dict:
        result = self._run("node", symbol, "--json", cwd=path)
        if result["success"] and result["stdout"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return {}

class CodeGraphPEEKIntegration:
    def __init__(self, codegraph: CodeGraphBridge, peek_manager=None):
        self.cg = codegraph
        self.peek = peek_manager
        self.cache_dir = CODEGRAPH_DIR / "peek_integration"
        self.cache_dir.mkdir(exist_ok=True)

    def query_with_cache(self, repo_path: str, query: str, task_type: str = "general") -> Dict:
        results = {
            "query": query,
            "task_type": task_type,
            "peek_results": [],
            "codegraph_results": [],
            "combined": [],
            "source": "hybrid",
        }

        if self.peek:
            peek_map_id = "codegraph-" + Path(repo_path).name
            peek_results = self.peek.query_map(peek_map_id, query)
            results["peek_results"] = peek_results

        cg_results = self.cg.search(query, limit=20)
        results["codegraph_results"] = cg_results

        combined = []
        seen = set()

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

    def cache_exploration(self, repo_path: str, query: str, exploration_result: Dict):
        if not self.peek:
            return

        peek_map_id = "codegraph-" + Path(repo_path).name

        trajectory = [{
            "turn_id": 0,
            "observation": "Exploring " + repo_path + " for " + query,
            "action": "CodeGraph search: " + query,
            "result": json.dumps(exploration_result, default=str)[:1000],
        }]

        if peek_map_id not in self.peek.maps:
            self.peek.create_map(
                map_id=peek_map_id,
                name="CodeGraph Cache: " + Path(repo_path).name,
                source=repo_path,
                budget=2048,
            )

        self.peek.update_map(peek_map_id, trajectory)

def register_commands() -> Dict[str, click.Command]:

    @click.command(name="codegraph")
    @click.option("--version", "show_version", is_flag=True)
    @click.option("--install", "install_codegraph", is_flag=True)
    @click.option("--status", "show_status", is_flag=True)
    def codegraph_cmd(show_version, install_codegraph, show_status):
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
                "Version: " + bridge.version + "\n"
                "Status: " + status + "\n"
                "Languages: 19+\n"
                "Frameworks: 14+\n"
                "Repository: https://github.com/colbymchenry/codegraph\n"
                "Cache: " + str(CODEGRAPH_DIR),
                title="ψ", border_style="bright_blue",
            )
            console.print(panel)
            return

        if show_status:
            result = bridge.status()
            if result["success"]:
                console.print(result["stdout"])
            else:
                console.print("[red]" + result['stderr'] + "[/red]")
            return

    @click.command(name="cg-init")
    @click.argument("path", default=".")
    @click.option("--interactive", "-i", is_flag=True, help="Interactive setup")
    def cg_init(path, interactive):
        bridge = CodeGraphBridge()
        result = bridge.init(path, interactive)
        if result["success"]:
            console.print("[green]✓ CodeGraph initialized in " + path + "[/green]")
            if result["stdout"]:
                console.print(result["stdout"])
        else:
            console.print("[red]✗ Error: " + result['stderr'] + "[/red]")

    @click.command(name="cg-index")
    @click.argument("path", default=".")
    @click.option("--force", is_flag=True, help="Force rebuild")
    def cg_index(path, force):
        bridge = CodeGraphBridge()
        console.print("[bold blue]Indexing " + path + "...[/bold blue]")
        result = bridge.index(path, force)
        if result["success"]:
            console.print("[green]✓ Index complete[/green]")
            if result["stdout"]:
                console.print(result["stdout"][:2000])
        else:
            console.print("[red]✗ Error: " + result['stderr'] + "[/red]")

    @click.command(name="cg-search")
    @click.argument("query")
    @click.option("--kind", help="Symbol kind filter")
    @click.option("--limit", "-l", default=20, help="Max results")
    def cg_search(query, kind, limit):
        bridge = CodeGraphBridge()
        results = bridge.search(query, kind, limit)

        if not results:
            console.print("[yellow]No results for '" + query + "'[/yellow]")
            return

        table = Table(title="CodeGraph Search: '" + query + "'")
        table.add_column("Name", style="cyan")
        table.add_column("Kind", style="green")
        table.add_column("File", style="white")
        table.add_column("Line", style="yellow")

        for r in results:
            file_path = r.get("file", "N/A")
            table.add_row(
                r.get("name", "N/A"),
                r.get("kind", "N/A"),
                file_path[-40:] if file_path else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-callers")
    @click.argument("symbol")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_callers(symbol, path):
        bridge = CodeGraphBridge()
        results = bridge.callers(symbol, path)

        if not results:
            console.print("[yellow]No callers found for '" + symbol + "'[/yellow]")
            return

        table = Table(title="Callers of '" + symbol + "'")
        table.add_column("Caller", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Line", style="yellow")

        for r in results:
            file_path = r.get("file", "N/A")
            table.add_row(
                r.get("name", "N/A"),
                file_path[-40:] if file_path else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-callees")
    @click.argument("symbol")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_callees(symbol, path):
        bridge = CodeGraphBridge()
        results = bridge.callees(symbol, path)

        if not results:
            console.print("[yellow]No callees found for '" + symbol + "'[/yellow]")
            return

        table = Table(title="Callees of '" + symbol + "'")
        table.add_column("Callee", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Line", style="yellow")

        for r in results:
            file_path = r.get("file", "N/A")
            table.add_row(
                r.get("name", "N/A"),
                file_path[-40:] if file_path else "N/A",
                str(r.get("line", "N/A")),
            )
        console.print(table)

    @click.command(name="cg-impact")
    @click.argument("symbol")
    @click.option("--depth", "-d", default=3, help="Max traversal depth")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_impact(symbol, depth, path):
        bridge = CodeGraphBridge()
        result = bridge.impact(symbol, depth, path)

        if not result:
            console.print("[yellow]No impact data for '" + symbol + "'[/yellow]")
            return

        tree = Tree("[bold]Impact Analysis: " + symbol + "[/bold] (depth=" + str(depth) + ")")

        if "affected" in result:
            affected = result["affected"]
            aff_tree = tree.add("[red]Affected (" + str(len(affected)) + ")[/red]")
            for item in affected[:20]:
                aff_tree.add("[cyan]" + item.get('name', 'N/A') + "[/cyan] [" + item.get('kind', 'N/A') + "]")

        if "callers" in result:
            callers = result["callers"]
            call_tree = tree.add("[yellow]Callers (" + str(len(callers)) + ")[/yellow]")
            for item in callers[:10]:
                call_tree.add(item.get("name", "N/A"))

        if "callees" in result:
            callees = result["callees"]
            cal_tree = tree.add("[green]Callees (" + str(len(callees)) + ")[/green]")
            for item in callees[:10]:
                cal_tree.add(item.get("name", "N/A"))

        console.print(tree)

    @click.command(name="cg-affected")
    @click.argument("symbol")
    @click.option("--depth", "-d", default=3, help="Max traversal depth")
    @click.option("--path", "-p", default=".", help="Repository path")
    def cg_affected(symbol, depth, path):
        bridge = CodeGraphBridge()
        result = bridge.impact(symbol, depth, path)

        if not result:
            console.print("[red]✗ No data for '" + symbol + "'[/red]")
            return

        affected = result.get("affected", [])
        console.print("[bold]Security Audit: Affected by '" + symbol + "'[/bold]")
        console.print("[dim]Depth: " + str(depth) + " | Total affected: " + str(len(affected)) + "[/dim]")

        if affected:
            table = Table(title="Affected Symbols")
            table.add_column("Symbol", style="cyan")
            table.add_column("Kind", style="green")
            table.add_column("File", style="white")
            table.add_column("Severity", style="red")

            for item in affected:
                kind = item.get("kind", "unknown")
                severity = "HIGH" if kind in ["function", "method", "class"] else "MEDIUM"
                file_path = item.get("file", "N/A")
                table.add_row(
                    item.get("name", "N/A"),
                    kind,
                    file_path[-30:] if file_path else "N/A",
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
        console.print("[bold blue]Hybrid Query (CodeGraph + PEEK): '" + query + "'[/bold blue]")
        console.print("[dim]Repository: " + repo + " | Task: " + task + "[/dim]")

        try:
            # Emulando a logica se nao houver PEEK disponivel globalmente para este script dummy
            peek = None
            has_peek = False
        except ImportError:
            peek = None
            has_peek = False

        bridge = CodeGraphBridge()
        integration = CodeGraphPEEKIntegration(bridge, peek)

        results = integration.query_with_cache(repo, query, task)

        console.print("\n[green]✓ Results: " + str(len(results['combined'])) + "[/green]")
        console.print("[dim]  PEEK: " + str(len(results['peek_results'])) + " | CodeGraph: " + str(len(results['codegraph_results'])) + "[/dim]")

        if results["combined"]:
            table = Table(title="Hybrid Results")
            table.add_column("Source", style="yellow")
            table.add_column("Name/Content", style="cyan")
            table.add_column("Meta", style="green")

            for item in results["combined"][:20]:
                if item["source"] == "peek":
                    table.add_row("PEEK", item["content"][:50], "p={:.2f}".format(item['priority']))
                else:
                    table.add_row("CodeGraph", item["name"], str(item['kind']) + ":" + str(item['line']))

            console.print(table)

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
"""

    def canonize(self):
        base_dir = tempfile.mkdtemp()
        s611_dir = os.path.join(base_dir, "611-CODEGRAPH")
        os.makedirs(s611_dir, exist_ok=True)

        files = {
            "__init__.py": self.init_py,
            "plugin.toml": self.plugin_toml,
            "codegraph_bridge.py": self.codegraph_bridge_py,
        }

        for path, content in files.items():
            full_path = os.path.join(s611_dir, path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        report = {
            "metadata": {
                "id": "611-CODEGRAPH",
                "name": "CodeGraph — Pre-indexed Code Knowledge Graph",
                "status": "CANONIZED",
                "canonical_seal": "6bd6a9cf2961d6bc0ab658da1eb80e181e5509935ce1345d3152ebccbfab855a",
                "date": "2026-05-24",
                "files_materialized": list(files.keys()),
                "temp_dir": base_dir
            }
        }

        fd, temp_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        return temp_path

if __name__ == "__main__":
    canonizer = Substrate611CodeGraph()
    path = canonizer.canonize()
    print("Substrate 611-CODEGRAPH canonized at:", path)
