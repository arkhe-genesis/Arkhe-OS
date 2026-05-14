from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.core.magic_arguments import argument, parse_argstring, magic_arguments
from IPython.display import display, Markdown, JSON
import asyncio
import nest_asyncio

nest_asyncio.apply()

class SafeCoreConnection:
    pass

from .universal_parser import UniversalParser, ParseContext

@magics_class
class ArkheMagics(Magics):
    def __init__(self, shell):
        super().__init__(shell)
        self.safe_core = SafeCoreConnection()
        self.parser = UniversalParser(
            temporal_chain=self._get_temporal_chain(),
            guardian=self._get_guardian(),
        )
        self._last_execution_seal = None
        self._parse_context = ParseContext()

    def _get_temporal_chain(self):
        return None

    def _get_guardian(self):
        return None

    async def _execute_parsed_command(self, cmd):
        return {"result": f"Executed {cmd.command}"}

    async def _execute_command(self, cmd, args):
        return {"result": f"Executed {cmd} with {args}"}

    def _run_async(self, coro):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.create_task(coro)
        else:
            return loop.run_until_complete(coro)

    @magic_arguments()
    @argument("command", nargs="?", default="status", help="Comando a executar")
    @argument("args", nargs="*", help="Argumentos do comando")
    @line_magic
    def arkhe(self, line: str):
        """Comando %arkhe: interface universal com parsing inteligente."""
        try:
            # Tentar parse universal primeiro
            tree = self.parser.parse(f"%arkhe {line}".strip(), self._parse_context)

            if tree.errors:
                # Mostrar erro com sugestão
                display(Markdown(f"❌ **Erro de parsing**: {tree.errors[0]}"))
                if self.parser.suggest_correction(line, self._parse_context):
                    display(Markdown(f"💡 {self.parser.suggest_correction(line, self._parse_context)}"))
                return

            # Extrair comando parseado
            if tree.root.node_type == 'magic_command':
                magic_cmd = tree.root.value
                result = self._run_async(self._execute_parsed_command(magic_cmd))
            elif tree.root.node_type == 'nl_intent':
                # Converter intenção NL para comando mágico
                nl_intent = tree.root.value
                if nl_intent.to_magic_command():
                    result = self._run_async(self._execute_parsed_command(nl_intent.to_magic_command()))
                else:
                    display(Markdown(f"❓ Intenção não mapeada: {nl_intent.intent_type}"))
                    return
            else:
                # Fallback para parser original
                args = parse_argstring(self.arkhe, line)
                result = self._run_async(self._execute_command(args.command, args.args))

            # Exibir resultado
            if isinstance(result, dict) and "error" in result:
                display(Markdown(f"❌ **Erro**: {result['error']}"))
            elif isinstance(result, dict):
                display(JSON(result, expanded=True))
            else:
                display(Markdown(str(result)))

            # Atualizar contexto
            self._parse_context.add_to_history(f"%arkhe {line}")

            return result

        except Exception as e:
            display(Markdown(f"❌ **Erro inesperado**: {e}"))
            return None

def load_ipython_extension(ipython):
    ipython.register_magics(ArkheMagics)
