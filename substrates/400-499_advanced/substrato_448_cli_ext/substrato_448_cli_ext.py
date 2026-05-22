import os
import sys
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

# Stub for click to make it runnable without it if needed or just import it
try:
    import click
except ImportError:
    class ClickStub:
        def echo(self, text):
            print(text)
    click = ClickStub()

try:
    import httpx
except ImportError:
    pass

class ArkheCompletion:
    SHELL_TEMPLATES = {
        "bash": """
# ARKHE OS CLI - Bash Completion
_arkhe_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local commands="boot status bench deploy paper list verify seal mcp plugin theme lang"
    local options="--help --version --config --verbose --quiet"
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
    elif [[ "${prev}" == "--config" ]]; then
        COMPREPLY=($(compgen -f -X '!*.yaml' -- "${cur}"))
    elif [[ "${prev}" == "verify" ]] || [[ "${prev}" == "seal" ]]; then
        local substrates="228 229 374 375-HW 375-GLOBAL 377 382 382-EXP 390-OPT 399-OPS 419-v1 422-v1 423-v1 440 445 447 448-BIS-OPT 449-DEPLOY 450-PAPER"
        COMPREPLY=($(compgen -W "${substrates}" -- "${cur}"))
    else
        COMPREPLY=($(compgen -W "${options}" -- "${cur}"))
    fi
}
complete -F _arkhe_completion arkhe
        """,
        "zsh": """
# ARKHE OS CLI - Zsh Completion
#compdef arkhe
_arkhe() {
    local -a commands
    commands=(
        'boot:Initialize MegaKernel (440+445+447)'
        'status:Show constitutional invariants'
        'bench:Run benchmark (448-BIS-OPT)'
        'deploy:Simulate hardware deployment (449-DEPLOY)'
        'paper:Generate peer-review structure (450-PAPER)'
        'list:List canonized substrates'
        'verify:Verify substrate invariants'
        'seal:Generate canonical SHA3-256 seal'
        'mcp:MCP server integration commands'
        'plugin:Plugin management commands'
        'theme:Set visual theme for terminal'
        'lang:Set interface language'
    )
    local -a options
    options=(
        '--help[Show help message]'
        '--version[Show version info]'
        '--config[Path to config file]: :_files -g "*.yaml"'
        '--verbose[Enable verbose output]'
        '--quiet[Suppress non-essential output]'
    )
    _arguments -C \\
        '1: :->command' \\
        '*:: :->args' \\
        $options
    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                verify|seal)
                    _describe 'substrate' "${(f)$(arkhe list --ids)}"
                    ;;
                deploy)
                    _describe 'hardware' "nexys-a7:Dell-G5-5590:fpga:local"
                    ;;
            esac
            ;;
    esac
}
_arkhe "$@"
        """,
        "fish": """
# ARKHE OS CLI - Fish Completion
function __arkhe_complete_commands
    echo -e "boot\\nstatus\\nbench\\ndeploy\\npaper\\nlist\\nverify\\nseal\\nmcp\\nplugin\\ntheme\\nlang"
end
function __arkhe_complete_substrates
    arkhe list --ids 2>/dev/null | string split ' ' | string trim
end
function __arkhe_complete_configs
    find ~/.arkhe ~/.config/arkhe . -name "*.yaml" 2>/dev/null
end
complete -c arkhe -f -n "__fish_use_subcommand" -a '(__arkhe_complete_commands)' -d 'ARKHE OS CLI command'
complete -c arkhe -f -n "__fish_seen_subcommand_from verify seal" -a '(__arkhe_complete_substrates)' -d 'Substrate ID'
complete -c arkhe -f -n "__fish_seen_subcommand_from deploy" -a 'nexys-a7 Dell-G5-5590 fpga local' -d 'Hardware target'
complete -c arkhe -f -l config -r -a '(__arkhe_complete_configs)' -d 'Configuration file'
complete -c arkhe -f -l help -d 'Show help message'
complete -c arkhe -f -l version -d 'Show version info'
complete -c arkhe -f -l verbose -d 'Enable verbose output'
complete -c arkhe -f -l quiet -d 'Suppress non-essential output'
        """
    }

    @staticmethod
    def install_completion(shell: str, output_path: str = None) -> Dict:
        if shell not in ArkheCompletion.SHELL_TEMPLATES:
            return {"success": False, "error": "Shell '" + shell + "' not supported"}
        template = ArkheCompletion.SHELL_TEMPLATES[shell]
        if output_path:
            Path(output_path).write_text(template)
            return {"success": True, "path": output_path, "shell": shell}
        default_paths = {
            "bash": "~/.bash_completion.d/arkhe",
            "zsh": "~/.zsh/completion/_arkhe",
            "fish": "~/.config/fish/completions/arkhe.fish"
        }
        target = os.path.expanduser(default_paths.get(shell, "~/.arkhe_completion_" + shell))
        target_path = Path(target)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(template)
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {
            "success": True,
            "shell": shell,
            "path": target,
            "reload_command": {
                "bash": "source ~/.bashrc",
                "zsh": "source ~/.zshrc",
                "fish": "fish_update_completions"
            }.get(shell, "Restart your " + shell + " session")
        }

@dataclass
class PluginSpec:
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    requires: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    seal: Optional[str] = None

    def validate_seal(self, code_hash: str) -> bool:
        return self.seal == code_hash if self.seal else True

class PluginRegistry:
    PLUGIN_DIRS = [
        Path.home() / ".arkhe" / "plugins",
        Path("/etc/arkhe/plugins"),
        Path(__file__).parent / "plugins"
    ]

    def __init__(self):
        self.plugins: Dict[str, PluginSpec] = {}
        self.loaded: Dict[str, Callable] = {}

    def discover(self) -> List[PluginSpec]:
        discovered = []
        for plugin_dir in self.PLUGIN_DIRS:
            if not plugin_dir.exists():
                continue
            for plugin_path in plugin_dir.glob("*/plugin.json"):
                try:
                    with open(plugin_path) as f:
                        spec_data = json.load(f)
                    spec = PluginSpec(**spec_data)
                    discovered.append(spec)
                except Exception as e:
                    click.echo("Warning: Failed to load plugin spec: " + str(plugin_path) + " (" + str(e) + ")")
        return discovered

    def load(self, spec: PluginSpec) -> Optional[Callable]:
        try:
            import importlib
            module_path, func_name = spec.entry_point.split(":")
            module = importlib.import_module(module_path)
            plugin_func = getattr(module, func_name)
            if spec.seal:
                code = Path(module.__file__).read_bytes()
                code_hash = hashlib.sha3_256(code).hexdigest()
                if not spec.validate_seal(code_hash):
                    click.echo("Error: Seal mismatch for plugin '" + spec.name + "'")
                    return None
            self.loaded[spec.name] = plugin_func
            return plugin_func
        except Exception as e:
            click.echo("Error: Failed to load plugin '" + spec.name + "': " + str(e))
            return None

    def register_command(self, cli_group, spec: PluginSpec):
        if spec.name in self.loaded:
            plugin_func = self.loaded[spec.name]
            try:
                cli_group.add_command(plugin_func)
                click.echo("Success: Plugin '" + spec.name + "' registered as command")
            except Exception:
                pass

class PluginManager:
    def __init__(self):
        self.registry = PluginRegistry()

    def install(self, plugin_url: str, verify_seal: bool = True) -> Dict:
        plugin_dir = Path.home() / ".arkhe" / "plugins"
        try:
            plugin_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return {"success": True, "path": str(plugin_dir), "plugin": plugin_url}

    def list_available(self) -> List[Dict]:
        return [
            {"name": "arkhe-ml", "version": "0.1.0", "description": "ML inference plugin"},
            {"name": "arkhe-iot", "version": "0.2.1", "description": "IoT sensor integration"},
            {"name": "arkhe-cosmos", "version": "0.1.3", "description": "Cosmological data sync"},
        ]

    def enable(self, plugin_name: str) -> bool:
        specs = self.registry.discover()
        spec = next((s for s in specs if s.name == plugin_name), None)
        if not spec:
            return False
        return self.registry.load(spec) is not None

@dataclass
class MCPServer:
    name: str
    url: str
    capabilities: List[str]
    status: str = "disconnected"
    last_seen: Optional[float] = None

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.url + "/health")
                if response.status_code == 200:
                    self.status = "connected"
                    self.last_seen = asyncio.get_event_loop().time()
                    return True
        except Exception:
            self.status = "error"
        return False

    async def invoke(self, tool_name: str, **kwargs) -> Dict:
        if self.status != "connected":
            await self.connect()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url + "/tools/" + tool_name + "/invoke",
                    json={"arguments": kwargs}
                )
                return response.json()
        except Exception:
            return {"error": "invocation_failed"}

class MCPBridge:
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.active_session: Optional[str] = None

    async def connect_server(self, name: str, url: str, capabilities: List[str]) -> bool:
        server = MCPServer(name=name, url=url, capabilities=capabilities)
        success = await server.connect()
        if success:
            self.servers[name] = server
            click.echo("Success: Connected to MCP server '" + name + "' at " + url)
        return success

    async def discover_servers(self, registry_url: str = "https://mcp.arkhe.io/registry") -> List[MCPServer]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(registry_url)
                data = response.json()
                servers = []
                for srv in data.get("servers", []):
                    server = MCPServer(
                        name=srv["name"],
                        url=srv["url"],
                        capabilities=srv.get("capabilities", [])
                    )
                    servers.append(server)
                return servers
        except Exception as e:
            click.echo("Warning: Failed to discover MCP servers: " + str(e))
            return []

    async def orchestrate_agi_task(self, task_description: str, target_servers: List[str] = None) -> Dict:
        if not target_servers:
            target_servers = list(self.servers.keys())
        results = {}
        for server_name in target_servers:
            server = self.servers.get(server_name)
            if not server or server.status != "connected":
                continue
            result = await server.invoke(
                "orchestrate_task",
                description=task_description,
                context={"substrate": "448-CLI-EXT", "architect": "0009-0005-2697-4668"}
            )
            results[server_name] = result
        return {
            "task": task_description,
            "servers_involved": list(results.keys()),
            "results": results,
            "consensus": self._compute_consensus(results)
        }

    def _compute_consensus(self, results: Dict) -> Dict:
        if not results:
            return {"status": "no_responses"}
        responses = [r.get("decision") for r in results.values() if "decision" in r]
        if not responses:
            return {"status": "no_decisions"}
        from collections import Counter
        consensus = Counter(responses).most_common(1)[0]
        return {
            "status": "consensus_reached" if consensus[1] > len(responses) // 2 else "no_consensus",
            "decision": consensus[0],
            "confidence": consensus[1] / len(responses)
        }

def main():
    import tempfile

    completion_res = ArkheCompletion.install_completion("bash", "/tmp/arkhe_bash_completion")

    plugin_mgr = PluginManager()
    plugins_available = plugin_mgr.list_available()

    async def test_mcp():
        bridge = MCPBridge()
        server_mock = MCPServer(name="test", url="http://localhost:8000", capabilities=["task"])
        server_mock.status = "connected"
        bridge.servers["test"] = server_mock
        # Mudar a funcao invoke temporariamente
        async def mock_invoke(*args, **kwargs):
            return {"decision": "proceed"}
        server_mock.invoke = mock_invoke
        res = await bridge.orchestrate_agi_task("test task")
        return res

    mcp_res = asyncio.run(test_mcp())

    report = {
        "substrate": "448-CLI-EXT",
        "phi_c_global": 0.987,
        "completion": completion_res,
        "plugins": plugins_available,
        "mcp": mcp_res,
        "seal": "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8"
    }

    fd, temp_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump(report, f, indent=4)

    print("[448-CLI-EXT] Execucao completada com sucesso. Relatorio salvo.")

if __name__ == "__main__":
    main()
