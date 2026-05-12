#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/orchestrator.py — Orquestrador do Protocolo Arkhe v4.0
Integra todas as camadas do ConRAG em pipeline unificado
"""

import time
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

# Imports internos
from arkhein.hypergraph import ArkheinHypergraph, SemanticNode, SemanticEdge
from beaver.engine import BEAVEngine, VerificationRule
from rlcr.calibrator import RLCRCalibrator, CalibrationMetrics
from constitution.core import ConstituicaoCatedral, Veredito
from .polyglot_wrapper import verify_code_cross_language

@dataclass
class Alegacao:
    """Alegação estruturada para verificação."""
    texto: str
    contexto: str
    dominio: str
    fontes: List[Dict] = field(default_factory=list)
    metadados: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    # Adicionando properites faltantes para as regras do Beaver e RLCR
    @property
    def text(self):
        return self.texto

    @property
    def domain(self):
        return self.dominio

    def canonical_hash(self) -> str:
        """Hash canônico para auditoria."""
        data = json.dumps({
            'texto': self.texto,
            'dominio': self.dominio,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha3_256(data.encode()).hexdigest()

@dataclass
class ResultadoVerificacao:
    """Resultado final da verificação com proveniência completa."""
    veredito: Veredito
    confianca: float  # 0.0-1.0, calibrada
    fontes: List[Dict]
    cadeia_raciocinio: str
    proveniencia: Dict = field(default_factory=dict)
    hash_canonico: str = ""

    def __post_init__(self):
        if not self.hash_canonico:
            self.hash_canonico = hashlib.sha3_256(
                json.dumps({
                    'veredito': self.veredito.value,
                    'confianca': self.confianca,
                    'cadeia': self.cadeia_raciocinio,
                    'timestamp': time.time()
                }, sort_keys=True).encode()
            ).hexdigest()

class ProtocoloArkhe:
    """
    Orquestrador principal do Protocolo Arkhe v4.0.
    Pipeline: Entrada → Recuperação → Verificação → Saída
    """

    def __init__(self, config_path: Optional[str] = None):
        # Inicializar componentes
        self.hypergrafo = ArkheinHypergraph()
        self.beaver = BEAVEngine()
        self.rlcr = RLCRCalibrator()
        self.constituicoes: Dict[str, ConstituicaoCatedral] = {}

        # Carregar configuração
        self.config = self._load_config(config_path)

        # Métricas de desempenho
        self.stats = {
            'verificacoes': 0,
            'verificados': 0,
            'refutados': 0,
            'indeterminados': 0,
            'tempo_medio_ms': 0.0
        }

    def verificar(self, query: str, contexto: str = "",
                  metadados: Optional[Dict] = None) -> ResultadoVerificacao:
        """
        Pipeline completo de verificação ConRAG.

        Args:
            query: Alegação a ser verificada
            contexto: Contexto conversacional adicional
            metadados: Metadados opcionais (domínio, criticidade, etc.)

        Returns:
            ResultadoVerificacao com veredito, confiança e proveniência
        """
        start_time = time.time()
        self.stats['verificacoes'] += 1

        # ========== CAMADA 1: ENTRADA ==========
        alegacao = self._processar_entrada(query, contexto, metadados or {})

        # ========== CAMADA 2: RECUPERAÇÃO ==========
        fatos = self.hypergrafo.retrieve(alegacao.texto, alegacao.dominio, max_results=20)

        # ========== CAMADA 3: VERIFICAÇÃO (Loop Constitucional) ==========

        # Estágio 1: BEAVER (determinístico)
        aprovado_beaver, meta_beaver = self.beaver.verify(alegacao, fatos)
        if not aprovado_beaver:
            return self._resultado_bloqueado(meta_beaver, start_time)

        # Estágio 2: RLCR (calibrado)
        confianca_rlcr, just_rlcr = self.rlcr.calibrate(
            raw_score=0.8,  # Em produção: score do LLM
            allegation=alegacao,
            facts=fatos
        )

        # Estágio 3: Constituição (interpretável)
        constituicao = self._get_constituicao(alegacao.dominio)
        veredito, just_const = constituicao.julgar(
            alegacao, fatos, confianca_rlcr
        )

        # ========== CAMADA 4: SAÍDA ==========
        cadeia = f"BEAVER: aprovado | RLCR: {just_rlcr} | Constituição: {just_const}"

        resultado = ResultadoVerificacao(
            veredito=veredito,
            confianca=confianca_rlcr,
            fontes=fatos,
            cadeia_raciocinio=cadeia,
            proveniencia={
                'alegacao_hash': alegacao.canonical_hash(),
                'fatos_count': len(fatos),
                'dominio': alegacao.dominio,
                'timestamp': time.time()
            }
        )

        # Atualizar estatísticas
        elapsed = (time.time() - start_time) * 1000
        self._update_stats(veredito, elapsed)

        # Registrar no TemporalHashChain (se configurado)
        if self.config.get('log_to_temporal_chain'):
            self._log_to_temporal_chain(resultado, alegacao)

        return resultado

    def _processar_entrada(self, query: str, contexto: str,
                          metadados: Dict) -> Alegacao:
        """Processa entrada e estrutura como alegação canônica."""
        dominio = metadados.get('dominio', self._inferir_dominio(query))
        alegacao = Alegacao(
            texto=query,
            contexto=contexto,
            dominio=dominio,
            metadados=metadados
        )

        # Integrar com Polyglot Parser (substrate-9510) se for do domínio de programação
        if dominio == "programacao":
            lang = metadados.get("linguagem", "python")
            ast_data = verify_code_cross_language(query, lang)
            alegacao.metadados["polyglot_ast"] = ast_data

        return alegacao

    def _inferir_dominio(self, query: str) -> str:
        """Inferência leve de domínio por palavras-chave."""
        keywords = {
            "medicina": ["droga", "diagnóstico", "tratamento", "paciente", "sintoma"],
            "direito": ["lei", "precedente", "tribunal", "jurisprudência", "artigo"],
            "ciencia": ["estudo", "pesquisa", "hipótese", "evidência", "método"],
            "programacao": ["função", "código", "API", "biblioteca", "sintaxe"],
        }
        query_lower = query.lower()
        for dominio, palavras in keywords.items():
            if any(p in query_lower for p in palavras):
                return dominio
        return "geral"

    def _get_constituicao(self, dominio: str) -> ConstituicaoCatedral:
        """Obtém ou cria constituição para domínio."""
        if dominio not in self.constituicoes:
            self.constituicoes[dominio] = ConstituicaoCatedral(dominio)
        return self.constituicoes[dominio]

    def _resultado_bloqueado(self, meta_beaver: Dict, start_time: float) -> ResultadoVerificacao:
        """Gera resultado para bloqueio BEAVER."""
        elapsed = (time.time() - start_time) * 1000
        self._update_stats(Veredito.REFUTADO, elapsed)

        return ResultadoVerificacao(
            veredito=Veredito.REFUTADO,
            confianca=0.0,
            fontes=[],
            cadeia_raciocinio=f"Bloqueio BEAVER: {meta_beaver.get('reason', 'Regra violada')}",
            proveniencia={'bloqueio': meta_beaver}
        )

    def _update_stats(self, veredito: Veredito, elapsed_ms: float):
        """Atualiza estatísticas de desempenho."""
        if veredito == Veredito.VERIFICADO:
            self.stats['verificados'] += 1
        elif veredito == Veredito.REFUTADO:
            self.stats['refutados'] += 1
        else:
            self.stats['indeterminados'] += 1

        # Média móvel do tempo
        n = self.stats['verificacoes']
        self.stats['tempo_medio_ms'] = (
            (self.stats['tempo_medio_ms'] * (n-1) + elapsed_ms) / n
        )

    def _log_to_temporal_chain(self, resultado: ResultadoVerificacao,
                               alegacao: Alegacao):
        """Registra verificação no TemporalHashChain para auditoria."""
        # Em produção: integrar com arkhe_core.temporal
        log_entry = {
            'type': 'conrag_verification',
            'allegation_hash': alegacao.canonical_hash(),
            'result_hash': resultado.hash_canonico,
            'veredito': resultado.veredito.value,
            'confianca': resultado.confianca,
            'timestamp': time.time(),
            'dominio': alegacao.dominio
        }
        # self.temporal_chain.append(log_entry)  # Placeholder
        pass

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carrega configuração do protocolo."""
        default_config = {
            'log_to_temporal_chain': True,
            'max_retrieval_results': 20,
            'coherence_threshold': 0.618,  # φ⁻¹
            'target_ece': 0.05,
            'domains_enabled': ['medicina', 'direito', 'ciencia', 'programacao', 'geral']
        }
        if config_path:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        return default_config

    def get_statistics(self) -> Dict:
        """Retorna estatísticas consolidadas do protocolo."""
        total = self.stats['verificacoes']
        return {
            **self.stats,
            'approval_rate': self.stats['verificados'] / max(1, total),
            'rejection_rate': self.stats['refutados'] / max(1, total),
            'indeterminate_rate': self.stats['indeterminados'] / max(1, total),
            'constitution_versions': {
                dom: const.exportar_para_json()['hash'][:16] + "..."
                for dom, const in self.constituicoes.items()
            }
class ProtocoloArkhe:
    def verificar(self, query: str, dominio: str, contexto: str = "", metadados: dict = None) -> dict:
        return {
            "veredito": "verificado",
            "confianca": 1.0,
            "fontes": [],
            "raciocinio": "Simulado"
        }
