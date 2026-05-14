# src/arkhe/layers/engineering/docs_generation.py
from arkhe.docs import generate_module_docs

def generate_full_docs(modules: list) -> str:
    full = "# ARKHE Full Documentation\n\n"
    for mod in modules:
        full += generate_module_docs(mod) + "\n\n"
    return full
