#!/usr/bin/env python3
"""
Julia-Parser — Parser de código Julia para ARKHE
Substrato 835 — JULIA-PARSER-BRIDGE
Arquiteto: ORCID 0009-0005-2697-4668
"""

import re, json, sys, os, base64, hashlib, tempfile
from typing import Dict, List, Any

class JuliaParser:
    def __init__(self):
        self.functions = {}
        self.macros = {}
        self.types = {}
        self.modules = {}

    def parse(self, code: str) -> Dict[str, Any]:
        result = {
            'functions': self._parse_functions(code),
            'macros': self._parse_macros(code),
            'types': self._parse_types(code),
            'modules': self._parse_modules(code),
            'imports': self._parse_imports(code),
            'exports': self._parse_exports(code),
        }
        return result

    def _parse_functions(self, code: str) -> List[Dict]:
        functions = []
        pattern = r'function\s+(\w+)\s*\((.*?)\)(.*?)end'
        for match in re.finditer(pattern, code, re.DOTALL):
            name, args, body = match.groups()
            functions.append({
                'name': name,
                'args': [a.strip() for a in args.split(',') if a.strip()],
                'body': body.strip(),
                'line': code[:match.start()].count(chr(10)) + 1
            })
        short_pattern = r'(\w+)\s*\((.*?)\)\s*=\s*(.+?)(?:\n|$)'
        for match in re.finditer(short_pattern, code):
            name, args, body = match.groups()
            if name not in [f['name'] for f in functions]:
                functions.append({
                    'name': name,
                    'args': [a.strip() for a in args.split(',') if a.strip()],
                    'body': body.strip(),
                    'line': code[:match.start()].count(chr(10)) + 1,
                    'short_form': True
                })
        return functions

    def _parse_macros(self, code: str) -> List[Dict]:
        macros = []
        pattern = r'macro\s+(\w+)\s*\((.*?)\)(.*?)end'
        for match in re.finditer(pattern, code, re.DOTALL):
            name, args, body = match.groups()
            macros.append({
                'name': name,
                'args': [a.strip() for a in args.split(',') if a.strip()],
                'body': body.strip()
            })
        return macros

    def _parse_types(self, code: str) -> List[Dict]:
        types = []
        struct_pattern = r'struct\s+(\w+)(.*?)end'
        for match in re.finditer(struct_pattern, code, re.DOTALL):
            name, body = match.groups()
            types.append({
                'name': name,
                'kind': 'struct',
                'fields': self._extract_fields(body)
            })
        abstract_pattern = r'abstract\s+type\s+(\w+)'
        for match in re.finditer(abstract_pattern, code):
            types.append({
                'name': match.group(1),
                'kind': 'abstract'
            })
        return types

    def _extract_fields(self, body: str) -> List[Dict]:
        fields = []
        for line in body.strip().split(chr(10)):
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(r'(\w+)\s*::\s*(\w+)', line)
                if match:
                    fields.append({
                        'name': match.group(1),
                        'type': match.group(2)
                    })
        return fields

    def _parse_modules(self, code: str) -> List[Dict]:
        modules = []
        pattern = r'module\s+(\w+)(.*?)end'
        for match in re.finditer(pattern, code, re.DOTALL):
            name, body = match.groups()
            modules.append({
                'name': name,
                'body': body.strip()
            })
        return modules

    def _parse_imports(self, code: str) -> List[str]:
        imports = []
        pattern = r'(?:using|import)\s+([\w.]+)'
        for match in re.finditer(pattern, code):
            imports.append(match.group(1))
        return imports

    def _parse_exports(self, code: str) -> List[str]:
        exports = []
        pattern = r'export\s+([\w,\s]+)'
        for match in re.finditer(pattern, code):
            exports.extend([e.strip() for e in match.group(1).split(',')])
        return exports

    def to_arkhe_ir(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        ir = {
            'language': 'julia',
            'version': '1.0',
            'substrato': '835-JULIA-PARSER-BRIDGE',
            'functions': [],
            'types': [],
            'modules': []
        }
        for func in parsed['functions']:
            ir['functions'].append({
                'name': func['name'],
                'parameters': func['args'],
                'return_type': 'inferred',
                'body_ast': self._julia_to_ast(func['body']),
                'coherence_index': self._compute_coherence(func)
            })
        for typ in parsed['types']:
            ir['types'].append({
                'name': typ['name'],
                'kind': typ['kind'],
                'fields': typ.get('fields', []),
                'is_mutable': False
            })
        return ir

    def _julia_to_ast(self, body: str) -> Dict:
        return {
            'type': 'block',
            'expressions': [line.strip() for line in body.split(chr(10)) if line.strip()]
        }

    def _compute_coherence(self, func: Dict) -> float:
        args_count = len(func['args'])
        body_lines = len([l for l in func['body'].split(chr(10)) if l.strip()])
        if body_lines == 0:
            return 1.0
        return min(1.0, args_count / body_lines + 0.5)

class Substrate835JuliaParserBridge:
    def __init__(self):
        with open(__file__, "rb") as f:
            script_content = f.read()

        b64_script = base64.b64encode(script_content).decode("utf-8")

        self.report = {
            "ID": "835",
            "Name": "JULIA-PARSER-BRIDGE",
            "Title": "Julia Code Parser for ARKHE",
            "Description": "Parses Julia code into ARKHE IR with Kuramoto coherence evaluation.",
            "Architect": "ORCID 0009-0005-2697-4668",
            "Files": {
                "substrato_835_julia_parser_bridge.py": b64_script
            }
        }

    def compute_seal(self):
        data_to_hash = self.report.copy()
        data_to_hash.pop("Seal_SHA3_256", None)
        payload = json.dumps(data_to_hash, sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_256(payload.encode('utf-8')).hexdigest()

    def canonize(self):
        self.report["Seal_SHA3_256"] = self.compute_seal()

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_835_", text=True)
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(self.report, f, indent=4, ensure_ascii=False)

        print("Canonized JULIA-PARSER-BRIDGE. Report saved to: " + path)
        print("Seal SHA3-256: " + self.report["Seal_SHA3_256"])
        return path

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Julia-Parser ARKHE')
    parser.add_argument('--file', help='Arquivo .jl para parse')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--ir', action='store_true', help='Output ARKHE IR')
    parser.add_argument('--canonize', action='store_true', help='Canonize substrate')
    args = parser.parse_args()

    if args.canonize:
        sub = Substrate835JuliaParserBridge()
        sub.canonize()
        return

    if not args.file:
        print("Provide --file for parsing or --canonize to canonize")
        return

    with open(args.file, 'r') as f:
        code = f.read()

    jp = JuliaParser()
    parsed = jp.parse(code)

    if args.ir:
        ir = jp.to_arkhe_ir(parsed)
        print(json.dumps(ir, indent=2))
    elif args.json:
        print(json.dumps(parsed, indent=2))
    else:
        print("Funcoes: " + str(len(parsed['functions'])))
        print("Macros: " + str(len(parsed['macros'])))
        print("Tipos: " + str(len(parsed['types'])))
        print("Modulos: " + str(len(parsed['modules'])))
        print("Imports: " + str(parsed['imports']))
        for func in parsed['functions']:
            print("  -> " + func['name'] + "(" + ", ".join(func['args']) + ")")

if __name__ == '__main__':
    main()
