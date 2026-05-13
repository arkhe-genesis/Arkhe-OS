# src/arkhe/layers/engineering/sdk_wrapper.py
from arkhe.layers.polyglot import PolyglotLexer, GrammarPool, TranspilerCore
from arkhe.compiler import ArkCompiler

class UnifiedSDK:
    def __init__(self):
        self.pool = GrammarPool()
        self.transpiler = TranspilerCore(self.pool)
        self.compiler = ArkCompiler()

    def run(self, code: str, language: str = "python") -> dict:
        # execution via polyglot: parse to UAST, transpile to Rust, execute
        # (simulation: compile with ark compiler)
        if language == "ark":
            return self.compiler.compile(code)
        else:
            uast = self.transpiler.transpile(code, language, "rust")
            return {"status": "transpiled", "uast_hash": uast.compute_hash()}
