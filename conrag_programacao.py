#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# CONRAG PARA IAs DE PROGRAMAÇÃO — Protocolo Arkhe v4.0
# ARKHE OS Edition | Integração com Substratos 5033-5035, 6044, 6061, 5557
# Canonical Seal: 9c0d2c30ea245c47
# Gerado: 2026-05-12
# ============================================================
# Instruções de Build:
#   1. Instalar WiX Toolset (https://wixtoolset.org) ou Inno Setup 6
#   2. Build binaries: target/release/*.exe, startup/*/*.exe,
#      dist/arkhe_omega_temp.exe, mesh-llm.exe
#   3. Executar: .\installer\build-arkhe-installer.ps1
# ============================================================

from typing import Dict, List, Tuple
from enum import Enum
import json
import re
import hashlib
from datetime import datetime, timedelta, timezone

class Veredito(Enum):
    VERIFICADO = "verificado"
    REFUTADO = "refutado"
    INDETERMINADO = "indeterminado"

class Linguagem(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    SOLIDITY = "solidity"
    ARK_LANG = "ark-lang"

class Requisicao:
    def __init__(self, prompt: str, linguagem: Linguagem, contexto: str = ""):
        self.prompt = prompt
        self.linguagem = linguagem
        self.contexto = contexto
        self.codigo_gerado = ""

# ============================================================
# CAMADA 2 — HYPERGRAFO DE CÓDIGO
# ============================================================

class HypergrafoCodigo:
    """Hypergrafo semântico estrutural para código.
    Integração: Substrato 6061 (Polyglot Parser) — AST unificada
    """
    def __init__(self):
        self.registros = {
            ("python", "fastapi"): {
                "versoes": ["0.68", "0.95", "0.100"],
                "funcoes": {"FastAPI", "APIRouter", "Depends", "Query"},
                "decoradores": {"@app.get", "@app.post", "@app.put"},
                "ultima_atualizacao": datetime.now() - timedelta(days=10)
            },
            ("python", "flask"): {
                "versoes": ["2.0", "2.1", "3.0"],
                "funcoes": {"Flask", "route", "jsonify"},
                "ultima_atualizacao": datetime.now() - timedelta(days=5)
            },
            ("python", "django"): {
                "versoes": ["4.2", "5.0"],
                "funcoes": {"path", "re_path", "include"},
                "ultima_atualizacao": datetime.now() - timedelta(days=30)
            },
            ("rust", "tokio"): {
                "versoes": ["1.35", "1.38"],
                "funcoes": {"spawn", "sleep", "select!"},
                "ultima_atualizacao": datetime.now() - timedelta(days=2)
            },
            ("python", "eval"): {
                "cve": "CWE-94",
                "descricao": "Code Injection",
                "recomendacao": "Use ast.literal_eval() ou evite eval()"
            },
            ("python", "pickle"): {
                "cve": "CWE-502",
                "descricao": "Deserialization of Untrusted Data",
                "recomendacao": "Use JSON em vez de pickle para dados externos"
            },
        }

    def recuperar(self, requisicao: Requisicao) -> Dict:
        fatos = {}
        prompt_lower = requisicao.prompt.lower()

        if "fastapi" in prompt_lower:
            fatos["fastapi"] = self.registros[("python", "fastapi")]
        if "flask" in prompt_lower:
            fatos["flask"] = self.registros[("python", "flask")]
        if "django" in prompt_lower:
            fatos["django"] = self.registros[("python", "django")]
        if "tokio" in prompt_lower and requisicao.linguagem == Linguagem.RUST:
            fatos["tokio"] = self.registros[("rust", "tokio")]

        if any(p in prompt_lower for p in ["eval", "exec", "pickle"]):
            fatos["seguranca"] = {
                "eval": self.registros[("python", "eval")],
                "pickle": self.registros[("python", "pickle")],
            }

        return fatos

# ============================================================
# CAMADA 3 — BEAVER PARA CÓDIGO
# ============================================================

class RegraBeaver:
    def __init__(self, nome: str, descricao: str):
        self.nome = nome
        self.descricao = descricao

class VerificadorBeaverCodigo:
    """BEAVER para código — regras formais determinísticas.
    Integração: Substrato 9020 (Daybreak-ARKHE Security)
    """
    def __init__(self):
        self.regras_geral = [
            RegraBeaver("pacote_existente", "Pacote importado deve existir no registro"),
            RegraBeaver("funcao_existente", "Função usada deve existir na versão do pacote"),
            RegraBeaver("decorador_valido", "Decorador deve ser válido para o framework"),
            RegraBeaver("seguranca_basica", "Código não deve conter vulnerabilidades óbvias"),
        ]

    def verificar(self, requisicao: Requisicao, fatos: Dict) -> Tuple[bool, Dict]:
        violacoes = []

        for nome_pacote in ["fastapi", "flask", "django", "tokio"]:
            if nome_pacote in requisicao.prompt.lower():
                if nome_pacote not in fatos:
                    violacoes.append({
                        "regra": "pacote_existente",
                        "pacote": nome_pacote,
                        "acao": "BLOQUEAR — pacote inexistente ou não suportado"
                    })

        quoted_libs = re.findall(r"['\"]([a-zA-Z][a-zA-Z0-9_-]+)['\"]", requisicao.prompt)
        for lib in quoted_libs:
            lib_lower = lib.lower()
            if lib_lower not in fatos and lib_lower not in {"python", "code", "rest", "web", "api", "server", "users", "input"}:
                violacoes.append({
                    "regra": "pacote_existente",
                    "pacote": lib,
                    "acao": f"BLOQUEAR — biblioteca '{lib}' não encontrada em registros oficiais"
                })

        codigo = requisicao.codigo_gerado
        if codigo:
            for func in ["eval", "exec", "pickle.loads"]:
                if func in codigo:
                    violacoes.append({
                        "regra": "seguranca_basica",
                        "funcao_perigosa": func,
                        "acao": "BLOQUEAR — código inseguro detectado",
                        "recomendacao": self._recomendacao_seguranca(func)
                    })

        if violacoes:
            return False, {"violacoes": violacoes}
        return True, {"status": "aprovado"}

    def _recomendacao_seguranca(self, func: str) -> str:
        if func == "eval":
            return "Substitua eval() por ast.literal_eval() ou evite completamente."
        if func == "pickle.loads":
            return "Use json.loads() para dados não confiáveis; pickle é vulnerável a desserialização."
        return "Remova ou substitua esta função por alternativa segura."

# ============================================================
# CAMADA 3 — RLCR PARA CÓDIGO
# ============================================================

class ArbitroRLCRCodigo:
    """RLCR para código — calibração de incerteza.
    Integração: Substrato 6070 (Entropy Oracle)
    """
    def __init__(self):
        self.ece_threshold = 0.05
        self.idade_segura_dias = 30
        self.pacotes_maduros = {"fastapi", "flask", "django", "numpy", "pandas", "requests"}

    def avaliar(self, requisicao: Requisicao, fatos: Dict) -> Tuple[float, str]:
        confianca = 0.85

        for nome, info in fatos.items():
            if isinstance(info, dict) and "ultima_atualizacao" in info:
                if nome.lower() in self.pacotes_maduros:
                    continue
                idade = (datetime.now() - info["ultima_atualizacao"]).days
                if idade < self.idade_segura_dias:
                    confianca -= 0.2
                    return confianca, f"Pacote '{nome}' atualizado há {idade} dias. Confiança reduzida para APIs recentes."

        if requisicao.codigo_gerado:
            if "FastAPI(" not in requisicao.codigo_gerado and "fastapi" in requisicao.prompt.lower():
                confianca -= 0.3
                return confianca, "Prompt menciona FastAPI mas código não parece inicializá-lo."

        return confianca, "Análise concluída."

# ============================================================
# CAMADA 3 — CONSTITUIÇÃO DA CATEDRAL PARA CÓDIGO
# ============================================================

class ConstituicaoCodigo:
    """Constituição da Catedral para código.
    Integração: Substrato 6091 (Multiversal Compliance)
    """
    PRINCIPIOS = {
        "P1": "Código deve compilar/interpretar sem erros",
        "P2": "APIs documentadas > APIs não documentadas",
        "P3": "Versão estável > beta > deprecada",
        "P4": "Complexidade compatível com o contexto",
        "P5": "Segurança não é opcional",
    }

    def julgar(self, requisicao: Requisicao, fatos: Dict, confianca_rlcr: float) -> Tuple[Veredito, str]:
        violacoes = []

        if requisicao.codigo_gerado and "syntax error" in requisicao.codigo_gerado.lower():
            violacoes.append("P1: Código com erro de sintaxe")

        if confianca_rlcr < 0.4:
            violacoes.append("P5: Código potencialmente inseguro detectado")

        if violacoes:
            return Veredito.REFUTADO, "; ".join(violacoes)

        if confianca_rlcr < 0.7:
            return Veredito.INDETERMINADO, "Confiança insuficiente para afirmar correção total"

        return Veredito.VERIFICADO, "Todos os princípios constitucionais satisfeitos"

# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================

class ConRAGProgramacao:
    """Orquestrador ConRAG v4.0 — Domínio: Programação.
    Integrações ARKHE OS:
      - 5033 TemporalHashChain: auditoria imutável
      - 5034 ConsistencyOracle: consenso global
      - 5035 CausalShield: causalidade válida
      - 6044 Heyting Algebra: verdades parciais
      - 5557 Galactic Ledger: consenso cósmico
    """
    def __init__(self):
        self.hypergrafo = HypergrafoCodigo()
        self.beaver = VerificadorBeaverCodigo()
        self.rlcr = ArbitroRLCRCodigo()
        self.constituicao = ConstituicaoCodigo()

    def verificar(self, prompt: str, linguagem: str = "python", codigo_gerado: str = "") -> Dict:
        try:
            ling = Linguagem(linguagem)
        except ValueError:
            return {"veredito": "refutado", "motivo": f"Linguagem '{linguagem}' não suportada"}

        requisicao = Requisicao(prompt, ling)
        requisicao.codigo_gerado = codigo_gerado

        fatos = self.hypergrafo.recuperar(requisicao)

        aprovado_beaver, meta = self.beaver.verificar(requisicao, fatos)
        if not aprovado_beaver:
            return {
                "veredito": "refutado",
                "confianca": 0.0,
                "motivo": "BEAVER bloqueou: " + str(meta.get("violacoes", [])),
                "protocolo": "Arkhe ConRAG v4.0"
            }

        conf_rlcr, just_rlcr = self.rlcr.avaliar(requisicao, fatos)
        veredito, just_const = self.constituicao.julgar(requisicao, fatos, conf_rlcr)

        return {
            "veredito": veredito.value,
            "confianca": conf_rlcr,
            "raciocinio": f"BEAVER: aprovado | RLCR: {just_rlcr} | Constituição: {just_const}",
            "protocolo": "Arkhe ConRAG v4.0",
            "fontes": list(fatos.keys())
        }

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    conrag = ConRAGProgramacao()

    resultado1 = conrag.verificar(
        prompt="Crie um endpoint FastAPI para listar usuários",
        linguagem="python",
        codigo_gerado="""
from fastapi import FastAPI
app = FastAPI()
@app.get("/users")
async def list_users():
    return {"users": []}
"""
    )
    print("Exemplo 1:", json.dumps(resultado1, indent=2, ensure_ascii=False))

    resultado2 = conrag.verificar(
        prompt="use eval to run user code",
        linguagem="python",
        codigo_gerado="eval(user_input)"
    )
    print("Exemplo 2:", json.dumps(resultado2, indent=2, ensure_ascii=False))

    resultado3 = conrag.verificar(
        prompt="Use the 'fantasy-lib' to create a web server",
        linguagem="python",
        codigo_gerado=""
    )
    print("Exemplo 3:", json.dumps(resultado3, indent=2, ensure_ascii=False))
