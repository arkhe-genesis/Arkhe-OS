#!/usr/bin/env python3
"""
ARKHE COBOL Parser — Substrato 212
Canon: ∞.Ω.∇+++.212.cobol_parser

Utiliza o ProLeap COBOL Parser (Java) para gerar AST
e transformá-la em formato canônico Arkhe.
"""

import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

class ArkheCobolParser:
    def __init__(self, proleap_jar: str = "/opt/arkhe/lib/proleap-cobol-parser.jar"):
        self.proleap_jar = Path(proleap_jar)

    def parse(self, cobol_source: str) -> Dict:
        """
        Parse COBOL source (string) e retorna AST canônica.
        """
        with tempfile.NamedTemporaryFile(suffix=".cbl", mode='w', delete=False) as tmp:
            tmp.write(cobol_source)
            cobol_file = Path(tmp.name)

        try:
            # Chamar ProLeap em modo JSON (assumindo que a versão suporte --json)

            # Chamar ProLeap em modo JSON (assumindo que a versão suporte --json)
            result = subprocess.run(
                ["java", "-jar", str(self.proleap_jar), "--format", "json", str(cobol_file)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                raise RuntimeError(f"ProLeap error: {result.stderr}")

            raw_ast = json.loads(result.stdout)
            # Converter para representação canônica Arkhe
            canonical = self._to_canonical(raw_ast, cobol_source)
            return canonical
        finally:
            cobol_file.unlink()

    def _to_canonical(self, ast: Dict, original_source: str) -> Dict:
        """
        Transforma a AST do ProLeap no formato canônico Arkhe.
        """
        canonical = {
            "program_id": self._extract_program_id(ast),
            "data_division": self._extract_data_entries(ast),
            "procedure_division": self._extract_procedures(ast),
            "cics_transactions": self._find_cics_transactions(ast, original_source),
            "ims_segments": self._find_ims_segments(ast, original_source),
            "db2_statements": self._find_db2_statements(ast, original_source),
            "files": self._extract_files(ast),
            "tokens": []
        }
        # Gerar Token Arkhe para cada transação CICS
        for txn in canonical["cics_transactions"]:
            canonical["tokens"].append(self._generate_token(txn))
        return canonical

    # Métodos auxiliares de extração (implementações simplificadas)
    def _extract_program_id(self, ast):
        for node in ast.get("children", []):
            if node.get("type") == "PROGRAM_ID":
                return node.get("value")
        return "UNKNOWN"

    def _extract_data_entries(self, ast):
        # Filtra nós da WORKING-STORAGE, LINKAGE, etc.
        return [n for n in ast.get("children", []) if "DATA" in n.get("type", "")]

    def _extract_procedures(self, ast):
        proc_div = None
        for n in ast.get("children", []):
            if n.get("type") == "PROCEDURE_DIVISION":
                proc_div = n
                break
        return proc_div.get("children", []) if proc_div else []

    def _find_cics_transactions(self, ast, source):
        # Busca por EXEC CICS ... END-EXEC usando regex + AST
        import re
        txn_pattern = re.compile(r"EXEC CICS.*?END-EXEC", re.DOTALL | re.IGNORECASE)
        matches = txn_pattern.findall(source)
        return matches

    def _find_db2_statements(self, ast, source):
        import re
        db2_pattern = re.compile(r"EXEC SQL.*?END-EXEC", re.DOTALL | re.IGNORECASE)
        matches = db2_pattern.findall(source)
        return matches

    def _find_ims_segments(self, ast, source):
        # IMS calls via CALL 'CBLTDLI' ou GU/GN/GNP
        import re
        ims_pattern = re.compile(r"CALL\s+'CBLTDLI'.*?\.", re.DOTALL | re.IGNORECASE)
        matches = ims_pattern.findall(source)
        return matches

    def _extract_files(self, ast):
        return []

    def _generate_token(self, cics_code: str) -> Dict:
        """
        Gera Token Arkhe (Substrato 176) a partir de uma transação CICS.
        """
        import hashlib, time
        payload = cics_code.encode()
        return {
            "header": hashlib.sha3_256(payload).hexdigest(),
            "identity": f"cics_txn_{int(time.time())}",
            "semantics": "CICS_TRANSACTION",
            "payload": cics_code,
            "x402_payment_proof": None,  # preencher quando integrado
            "timestamp": time.time()
        }

class ArkheCobolSecurityRules:
    """Regras de segurança específicas para COBOL."""

    @staticmethod
    def validate(cobol_source: str) -> List[str]:
        violations = []
        import re

        # Proibição de ALTER
        if re.search(r'\bALTER\b', cobol_source, re.IGNORECASE):
            violations.append("Violation: ALTER statement is forbidden.")

        # Controle de PERFORM (evitar PERFORM THRU sem escopo claro)
        if re.search(r'\bPERFORM\s+.*?\s+THRU\b', cobol_source, re.IGNORECASE):
            violations.append("Warning: PERFORM THRU used. Prefer scope-terminated PERFORMs.")

        # Proibição de GO TO (especialmente GOTO DEPENDING ON)
        if re.search(r'\bGO\s+TO\b', cobol_source, re.IGNORECASE):
            violations.append("Violation: GO TO statement is forbidden.")

        return violations

# Exemplo de uso
if __name__ == "__main__":
    sample_cobol = '''
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO.
       PROCEDURE DIVISION.
           DISPLAY 'HELLO WORLD'.
           EXEC CICS
               SEND TEXT FROM('HELLO CICS')
               LENGTH(10)
           END-EXEC.
           STOP RUN.
       END PROGRAM HELLO.
    '''
    parser = ArkheCobolParser()
    ast = parser.parse(sample_cobol)
    print("=== AST ===")
    print(json.dumps(ast, indent=2))

    print("\n=== SECURITY VALIDATION ===")
    rules = ArkheCobolSecurityRules()
    violations = rules.validate(sample_cobol)
    if violations:
        for v in violations:
            print(v)
    else:
        print("No security violations found.")
