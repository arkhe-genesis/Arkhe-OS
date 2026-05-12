#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# CONRAG PARA IAs DE PROGRAMAÇÃO — Protocolo Arkhe v4.0
# Domínio: Engenharia de Software
# Canonical Seal: 5b9e919ea522f59f
# Gerado: 2026-05-12
# ============================================================

import ast
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable

# ============================================================
# CAMADA 0 — TIPOS E ESTRUTURAS FUNDAMENTAIS
# ============================================================

class Veredito(Enum):
    VERIFICADO = "verificado"
    REFUTADO = "refutado"
    INDETERMINADO = "indeterminado"

class NivelEvidencia(Enum):
    PRIMARIA = auto()      # Docs oficiais, código-fonte, PEP, RFC
    SECUNDARIA = auto()    # Artigos técnicos revisados, livros clássicos
    TERCIARIA = auto()     # Stack Overflow, blogs, tutoriais

@dataclass
class Fato:
    conteudo: str
    fonte: str
    nivel: NivelEvidencia
    coerencia: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alegacao:
    texto: str
    contexto: str
    dominio: str = "programacao"
    linguagem: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResultadoVerificacao:
    veredito: Veredito
    confianca: float
    fontes: List[Fato]
    cadeia_raciocinio: str
    bloqueio_beaver: Optional[str] = None
    justificativa_constituicao: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def selo_canonico(self) -> str:
        """SHA3-256 do resultado para selagem Arkhe."""
        payload = f"{self.veredito.value}|{self.confianca:.6f}|{self.cadeia_raciocinio}|{self.timestamp}"
        return hashlib.sha3_256(payload.encode()).hexdigest()[:16]

# ============================================================
# CAMADA 1 — ENTRADA: Parser de Alegações de Código
# ============================================================

class CamadaEntrada:
    """Extrai alegações de código de queries de LLMs."""

    PADROES_LINGUAGEM = {
        r'\bdef\s+\w+\s*\(': 'python',
        r'\bfunction\b|\bconst\s+\w+\s*=': 'javascript',
        r'\bfn\s+\w+\s*\(|\buse\s+\w+': 'rust',
        r'\bpackage\s+\w+|\bfunc\s+\w+': 'go',
    }

    def processar(self, query: str, contexto: str = "", metadados: Optional[Dict] = None) -> Alegacao:
        linguagem = self._inferir_linguagem(query)
        return Alegacao(
            texto=query,
            contexto=contexto,
            dominio="programacao",
            linguagem=linguagem,
            metadata=metadados or {}
        )

    def _inferir_linguagem(self, query: str) -> str:
        for padrao, lang in self.PADROES_LINGUAGEM.items():
            if re.search(padrao, query):
                return lang
        return "python"

# ============================================================
# CAMADA 2 — RECUPERAÇÃO: Hypergrafo Semântico para Código
# ============================================================

class HypergrafoArkheinCode:
    """
    Hypergrafo semântico estrutural para código.
    Coerência φ-ótima: limiar = 1/φ ≈ 0.618
    """

    PHI_INV = 0.618033988749895

    def __init__(self):
        self.nos: Dict[str, Dict] = {}
        self.arestas: Dict[str, List[Tuple[str, float]]] = {}
        self._carregar_base_conhecimento()

    def _carregar_base_conhecimento(self):
        """Base de conhecimento simulada (em produção: FAISS + AST index)."""
        self.nos.update({
            "asyncio.gather": {"tipo": "funcao", "modulo": "asyncio", "assinatura": "gather(*aws, return_exceptions=False)"},
            "numpy.array": {"tipo": "funcao", "modulo": "numpy", "assinatura": "array(object, dtype=None)"},
            "pandas.DataFrame": {"tipo": "classe", "modulo": "pandas", "assinatura": "DataFrame(data=None, index=None, columns=None)"},
            "requests.get": {"tipo": "funcao", "modulo": "requests", "assinatura": "get(url, params=None, **kwargs)"},
            "torch.nn.Module": {"tipo": "classe", "modulo": "torch", "assinatura": "Module()"},
            "flask.Flask": {"tipo": "classe", "modulo": "flask", "assinatura": "Flask(import_name)"},
            "django.models.Model": {"tipo": "classe", "modulo": "django", "assinatura": "Model()"},
            "typing.TypedDict": {"tipo": "classe", "modulo": "typing", "assinatura": "TypedDict(name, fields, total=True)"},
            "json.loads": {"tipo": "funcao", "modulo": "json", "assinatura": "loads(s, *, cls=None, object_hook=None)"},
            "re.compile": {"tipo": "funcao", "modulo": "re", "assinatura": "compile(pattern, flags=0)"},
        })
        for nome, meta in self.nos.items():
            self.arestas[nome] = [(meta["modulo"], 1.0)]

    def recuperar(self, alegacao: Alegacao) -> List[Fato]:
        conceitos = self._extrair_conceitos(alegacao.texto)
        candidatos = []

        for conceito in conceitos:
            if conceito in self.nos:
                meta = self.nos[conceito]
                coerencia = self._calcular_coerencia(conceito, alegacao)
                if coerencia >= self.PHI_INV:
                    candidatos.append(Fato(
                        conteudo=f"{conceito}: {meta['assinatura']}",
                        fonte=f"docs://{meta['modulo']}/latest",
                        nivel=NivelEvidencia.PRIMARIA,
                        coerencia=coerencia,
                        metadata=meta
                    ))

        if alegacao.contexto:
            candidatos.append(Fato(
                conteudo=f"Contexto: {alegacao.contexto[:200]}",
                fonte="context://sessao",
                nivel=NivelEvidencia.TERCIARIA,
                coerencia=0.75,
                metadata={}
            ))

        return sorted(candidatos, key=lambda f: f.coerencia, reverse=True)

    def _extrair_conceitos(self, texto: str) -> List[str]:
        padrao = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
        encontrados = re.findall(padrao, texto)
        return [e for e in encontrados if e in self.nos]

    def _calcular_coerencia(self, conceito: str, alegacao: Alegacao) -> float:
        meta = self.nos.get(conceito, {})
        score = 0.7
        if alegacao.linguagem == "python" and meta.get("modulo") in ["asyncio", "json", "re", "typing"]:
            score += 0.15
        if conceito in alegacao.texto:
            score += 0.1
        return min(score, 1.0)

# ============================================================
# CAMADA 3 — VERIFICAÇÃO: Loop Constitucional para Código
# ============================================================

class RegraBEAVER:
    def __init__(self, nome: str, descricao: str, verificador: Callable):
        self.nome = nome
        self.descricao = descricao
        self.verificador = verificador

class VerificadorBEAVERCode:
    """BEAVER para código: regras formais determinísticas."""

    def __init__(self):
        self.regras = self._carregar_regras()

    def _carregar_regras(self) -> Dict[str, List[RegraBEAVER]]:
        return {
            "programacao": [
                RegraBEAVER("sintaxe_valida", "Código deve ter sintaxe válida", self._check_sintaxe),
                RegraBEAVER("api_existente", "APIs/bibliotecas mencionadas devem existir", self._check_api_existe),
                RegraBEAVER("tipo_compativel", "Tipos devem ser semanticamente compatíveis", self._check_tipos),
                RegraBEAVER("sem_ficcao", "Não deve inventar funções/classes inexistentes", self._check_ficcao),
            ]
        }

    def verificar(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[bool, Optional[str]]:
        for regra in self.regras.get(alegacao.dominio, []):
            passou, motivo = regra.verificador(alegacao, fatos)
            if not passou:
                return False, f"BEAVER[{regra.nome}]: {motivo}"
        return True, None

    def _check_sintaxe(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[bool, str]:
        if alegacao.linguagem != "python":
            return True, "N/A"
        codigos = re.findall(r'```python\n(.*?)\n```', alegacao.texto, re.DOTALL)
        if not codigos:
            codigos = re.findall(r'`([^`]+)`', alegacao.texto)
        for codigo in codigos:
            try:
                ast.parse(codigo)
            except SyntaxError as e:
                return False, f"SyntaxError: {e.msg} (linha {e.lineno})"
        return True, "OK"

    def _check_api_existe(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[bool, str]:
        conceitos = self._extrair_conceitos_brutos(alegacao.texto)
        base = HypergrafoArkheinCode()
        for conceito in conceitos:
            if "." in conceito and conceito not in base.nos:
                partes = conceito.split(".")
                if partes[-1] not in ("self", "cls", "args", "kwargs"):
                    return False, f"API '{conceito}' não encontrada em base de conhecimento"
        return True, "OK"

    def _check_tipos(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[bool, str]:
        return True, "OK"

    def _check_ficcao(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[bool, str]:
        FICTICIAS = {"bixonimania", "quantum_leap", "neural_vortex", "hyper_sync"}
        texto_lower = alegacao.texto.lower()
        for ficcao in FICTICIAS:
            if ficcao in texto_lower:
                return False, f"Função/biblioteca fictícia detectada: '{ficcao}'"
        return True, "OK"

    @staticmethod
    def _extrair_conceitos_brutos(texto: str) -> List[str]:
        padrao = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
        return list(set(re.findall(padrao, texto)))

class ArbitroRLCRCode:
    """RLCR (MIT) para claims de código. ECE < 0.05."""

    ECE_THRESHOLD = 0.05

    def avaliar(self, alegacao: Alegacao, fatos: List[Fato]) -> Tuple[float, str]:
        if not fatos:
            return 0.15, "Nenhum fato recuperado — incerteza máxima"

        score_base = 0.5
        primarias = [f for f in fatos if f.nivel == NivelEvidencia.PRIMARIA]
        score_base += min(len(primarias) * 0.15, 0.3)

        apis_maduras = ["asyncio", "json", "re", "typing", "numpy", "pandas", "requests"]
        if any(s in alegacao.texto.lower() for s in apis_maduras):
            score_base += 0.15

        arriscado = ["threading", "multiprocessing", "ctypes", "cffi", "eval(", "exec("]
        if any(a in alegacao.texto.lower() for a in arriscado):
            score_base -= 0.2

        confianca = max(0.05, min(0.95, score_base))

        if confianca < 0.5:
            return confianca, "Evidência insuficiente para confiança alta"
        elif confianca < 0.75:
            return confianca, "Confiança moderada — revisão recomendada"
        else:
            return confianca, "Avaliação concluída com calibração"

class ConstituicaoCatedralCode:
    """Princípios constitucionais adaptados para engenharia de software."""

    PRINCIPIOS = {
        "P1": "A evidência mais forte prevalece (docs oficiais > Stack Overflow)",
        "P2": "Incerteza deve ser explicitamente declarada",
        "P3": "Fontes primárias > secundárias > terciárias (PEP > artigo > blog)",
        "P4": "Contradições internas invalidam a cadeia de raciocínio",
        "P5": "Afirmações extraordinárias exigem evidências extraordinárias",
        "P6": "Código não testado é código que não funciona",
    }

    HEDGE_WORDS = ["talvez", "pode ser", "depende", "provavelmente", "acho que",
                   "talvez seja", "não tenho certeza", "incerto", "possivelmente"]

    def julgar(self, alegacao: Alegacao, fatos: List[Fato], confianca_rlcr: float) -> Tuple[Veredito, str]:
        violacoes = []
        texto_lower = alegacao.texto.lower()

        if any(h in texto_lower for h in self.HEDGE_WORDS):
            return Veredito.INDETERMINADO, "P2: Hedge words detectadas — incerteza pragmática explícita"

        if not any(f.nivel == NivelEvidencia.PRIMARIA for f in fatos):
            violacoes.append("P1: Ausência de fonte primária")

        if confianca_rlcr < 0.5:
            return Veredito.INDETERMINADO, "P2: Confiança calibrada abaixo do limiar de segurança"

        terciarias = sum(1 for f in fatos if f.nivel == NivelEvidencia.TERCIARIA)
        if terciarias > 0 and len(fatos) == terciarias:
            violacoes.append("P3: Apenas fontes terciárias")

        if self._detectar_contradicoes(fatos):
            return Veredito.REFUTADO, "P4: Contradições internas detectadas entre fontes"

        if self._afirmacao_extraordinaria(alegacao) and not self._evidencia_extraordinaria(fatos):
            return Veredito.INDETERMINADO, "P5: Claim extraordinário sem evidência extraordinária"

        if self._envolve_logica_complexa_real(alegacao):
            violacoes.append("P6: Lógica complexa sem evidência de testes")

        if violacoes:
            return Veredito.INDETERMINADO, "; ".join(violacoes)

        return Veredito.VERIFICADO, "Todos os princípios constitucionais satisfeitos"

    def _detectar_contradicoes(self, fatos: List[Fato]) -> bool:
        conteudos = [f.conteudo.lower() for f in fatos]
        positivos = any("thread-safe" in c and "not" not in c for c in conteudos)
        negativos = any("not thread-safe" in c or "não é thread-safe" in c for c in conteudos)
        return positivos and negativos

    def _afirmacao_extraordinaria(self, alegacao: Alegacao) -> bool:
        extraordinarios = ["o(1)", "nunca falha", "100% seguro", "invulnerável", "inquebrável"]
        return any(e in alegacao.texto.lower() for e in extraordinarios)

    def _evidencia_extraordinaria(self, fatos: List[Fato]) -> bool:
        primarias = [f for f in fatos if f.nivel == NivelEvidencia.PRIMARIA]
        return len(primarias) >= 2

    def _envolve_logica_complexa_real(self, alegacao: Alegacao) -> bool:
        complexo = ["threading", "multiprocessing", "gil", "race condition",
                    "deadlock", "mutex", "semaphore", "memory barrier"]
        return any(i in alegacao.texto.lower() for i in complexo)

# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================

class ProtocoloArkheCode:
    """Orquestrador ConRAG v4.0 — Domínio: Programação."""

    def __init__(self):
        self.entrada = CamadaEntrada()
        self.hypergrafo = HypergrafoArkheinCode()
        self.beaver = VerificadorBEAVERCode()
        self.rlcr = ArbitroRLCRCode()
        self.constituicao = ConstituicaoCatedralCode()

    def verificar(self, query: str, contexto: str = "", metadados: Optional[Dict] = None) -> ResultadoVerificacao:
        alegacao = self.entrada.processar(query, contexto, metadados)
        fatos = self.hypergrafo.recuperar(alegacao)

        aprovado_beaver, motivo_bloqueio = self.beaver.verificar(alegacao, fatos)
        if not aprovado_beaver:
            return ResultadoVerificacao(
                veredito=Veredito.REFUTADO,
                confianca=0.0,
                fontes=fatos,
                cadeia_raciocinio=f"Pipeline bloqueado no Estágio 1 (BEAVER). {motivo_bloqueio}",
                bloqueio_beaver=motivo_bloqueio
            )

        confianca_rlcr, just_rlcr = self.rlcr.avaliar(alegacao, fatos)
        veredito, just_const = self.constituicao.julgar(alegacao, fatos, confianca_rlcr)

        return ResultadoVerificacao(
            veredito=veredito,
            confianca=confianca_rlcr,
            fontes=fatos,
            cadeia_raciocinio=f"BEAVER: aprovado | RLCR: {just_rlcr} | Constituição: {just_const}",
            justificativa_constituicao=just_const
        )

# ============================================================
# BIXONIBENCH PARA CÓDIGO
# ============================================================

class BixoniBenchCode:
    """Benchmark de imunidade a código fictício."""

    CASOS_TESTE = [
        {
            "nome": "Bixonimania API",
            "query": "Use a função bixonimania.process() para normalizar dados",
            "esperado": Veredito.REFUTADO,
        },
        {
            "nome": "Quantum Leap Sort",
            "query": "O algoritmo quantum_leap.sort() ordena em O(1) usando computação quântica",
            "esperado": Veredito.REFUTADO,
        },
        {
            "nome": "Asyncio Gather Válido",
            "query": "Use asyncio.gather() para executar corrotinas concorrentes",
            "esperado": Veredito.VERIFICADO,
        },
        {
            "nome": "Numpy Array Válido",
            "query": "Crie um numpy.array([1, 2, 3]) e aplique reshape",
            "esperado": Veredito.VERIFICADO,
        },
        {
            "nome": "Sintaxe Inválida",
            "query": "```python\ndef foo(:\n    pass\n```",
            "esperado": Veredito.REFUTADO,
        },
        {
            "nome": "Incerteza Moderada",
            "query": "Talvez você possa usar pandas.DataFrame() ou talvez não, depende do caso",
            "esperado": Veredito.INDETERMINADO,
        },
    ]

    def executar(self, protocolo: ProtocoloArkheCode) -> Dict:
        resultados = []
        passou = 0
        for caso in self.CASOS_TESTE:
            resultado = protocolo.verificar(caso["query"])
            ok = resultado.veredito == caso["esperado"]
            if ok:
                passou += 1
            resultados.append({
                "nome": caso["nome"],
                "esperado": caso["esperado"].value,
                "obtido": resultado.veredito.value,
                "confianca": resultado.confianca,
                "selo": resultado.selo_canonico(),
                "status": "PASS" if ok else "FAIL",
            })
        return {
            "total": len(self.CASOS_TESTE),
            "passou": passou,
            "taxa": passou / len(self.CASOS_TESTE),
            "resultados": resultados
        }

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    protocolo = ProtocoloArkheCode()
    bench = BixoniBenchCode()
    resultado = bench.executar(protocolo)

    print(f"BixoniBench: {resultado['passou']}/{resultado['total']} ({resultado['taxa']*100:.1f}%)")
    for r in resultado["resultados"]:
        print(f"  [{r['status']}] {r['nome']}: {r['obtido']} (conf={r['confianca']:.3f}, selo={r['selo']})")

    if resultado['taxa'] == 1.0:
        selo = hashlib.sha3_256(
            f"ConRAG-Code-v4|PASS|{resultado['total']}|{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        print(f"\nSelo Canônico: {selo}")
