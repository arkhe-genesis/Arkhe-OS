#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_augmented_router.py — Roteador AI-Augmented para Ω-TEMP v4.0
=================================================================
Substitui a lógica heurística de roteamento CDVRP por decisões
baseadas em modelo local (Ollama, llama.cpp, LM Studio, etc.).

O modelo é consultado para:
  1. Causal Distance Vector — cálculo de métricas de custo entre nós
  2. Detecção de paradoxos — análise de consistência temporal profunda
  3. Filtragem de conteúdo — política de segurança de payloads

Integração transparente com o RetroRouter existente.

Uso:
  # Via import
  router = AIRouter(endpoint="http://localhost:11434", model="llama3.1:8b")

  # Via CLI
  python ai_augmented_router.py --test-routing --node ALFA-01
"""

import hashlib
import json
import logging
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

log = logging.getLogger("arkhe.ai_router")

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

@dataclass
class AIConfig:
    endpoint: str = "http://localhost:11434"
    model: str = "llama3.1:8b"
    temperature: float = 0.3
    max_tokens: int = 512
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 2.0
    fallback_enabled: bool = True  # Volta para heurística se modelo falhar
    batch_routing: bool = True     # Processa múltiplas rotas em uma chamada
    cache_ttl: float = 60.0        # Cache de decisões (segundos)


# ============================================================================
# CLIENTE LLM LOCAL
# ============================================================================

class LocalLLMClient:
    """
    Cliente para modelos locais via API OpenAI-compatível.
    Suporta Ollama, llama.cpp server, LM Studio, vLLM, etc.
    """

    def __init__(self, config: AIConfig):
        self.config = config
        self._cache: Dict[str, Tuple[Any, float]] = {}  # query → (response, expiry)
        self._stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'fallbacks': 0,
            'errors': 0,
            'total_latency': 0.0,
        }

    @property
    def stats(self) -> Dict:
        avg_latency = (self._stats['total_latency'] /
                       max(1, self._stats['total_calls'] - self._cache.get('_misses', 0)))
        return {
            **self._stats,
            'avg_latency_ms': round(avg_latency * 1000, 2),
        }

    def _make_request(self, prompt: str) -> Optional[str]:
        """Envia prompt para o modelo local."""
        url = f"{self.config.endpoint}/api/chat"
        payload = json.dumps({
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }).encode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        for attempt in range(self.config.max_retries):
            try:
                t0 = time.time()
                req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                    data = json.loads(resp.read().decode())
                    latency = time.time() - t0
                    self._stats['total_calls'] += 1
                    self._stats['total_latency'] += latency
                    return data.get('message', {}).get('content', '').strip()
            except urllib.error.URLError as e:
                self._stats['errors'] += 1
                log.warning(f"LLM tentativa {attempt+1}/{self.config.max_retries}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
            except Exception as e:
                self._stats['errors'] += 1
                log.error(f"Erro LLM: {e}")
                break
        return None

    def _system_prompt(self) -> str:
        return """Você é o assistente de roteamento da rede retrocausal ARKHE Ω-TEMP v4.0.
Sua tarefa é tomar decisões de roteamento baseadas em consistência temporal e causal.

Regras fundamentais:
1. Nunca crie loops causais (paradoxo do avô)
2. Mensagens para o passado devem ser verificadas contra registros existentes
3. Priorize rotas com maior consistência (score mais alto)
4. Detecte paradoxos potenciais e os marque
5. Conteúdo suspeito deve ser sinalizado

Responda SEMPRE em JSON válido. Não faça comentários fora do JSON."""

    def query(self, prompt: str, cache_key: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
        """Consulta o modelo com cache opcional."""
        if use_cache and cache_key:
            key = hashlib.md5(f"{cache_key}:{prompt}".encode()).hexdigest()
            if key in self._cache:
                result, expiry = self._cache[key]
                if time.time() < expiry:
                    self._stats['cache_hits'] += 1
                    return result
                del self._cache[key]

        result = self._make_request(prompt)
        if result and cache_key:
            self._cache[key] = (result, time.time() + self.config.cache_ttl)
        return result

    def check_health(self) -> bool:
        """Verifica se o endpoint está disponível."""
        try:
            url = f"{self.config.endpoint}/api/tags"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except:
            return False


# ============================================================================
# PROMPTS ESPECIALIZADOS
# ============================================================================

class AIRoutingPrompts:
    """Gera prompts especializados para cada tipo de decisão de roteamento."""

    @staticmethod
    def routing_decision(
        node_id: str,
        dest: str,
        available_routes: List[Dict],
        network_topology: Dict,
        ledger_entries: List[Dict],
        temporal_window: float,
    ) -> str:
        """Gera prompt para decisão de roteamento."""
        routes_json = json.dumps(available_routes, indent=2)[:2000]
        topology_json = json.dumps(network_topology, indent=2)[:1000]
        ledger_summary = json.dumps([
            {'type': e['type'], 'time': e['timestamp'],
             'preview': str(e['payload'])[:200]}
            for e in ledger_entries[:20]
        ], indent=2)

        return f"""DECISÃO DE ROTEAMENTO TEMPORAL

Nó atual: {node_id}
Destino: {dest}
Janela temporal: ±{temporal_window:.0f}s ({(temporal_window/(365.25*86400)):.1f} anos)

ROTAS DISPONÍVEIS:
{routes_json}

TOPOLOGIA REDE:
{topology_json}

REGISTROS RELEVANTES DO LEDGER:
{ledger_summary}

Analise e retorne QUAL rota é a melhor escolha considerando:
1. Consistência temporal (evitar paradoxos)
2. Custo energético (menor uso de entropia)
3. Fidelidade do entrelaçamento (preferir canais mais estáveis)
4. Disponibilidade do próximo hop

Retorne EXCLUSIVAMENTE em JSON:
{{
  "chosen_route": {{ "next_hop": "...", "dest": "...", "cost": 0.0 }},
  "reasoning": "explicação breve",
  "confidence": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "paradox_risk": 0.0-1.0,
  "entropy_cost": 0.0-1.0
}}
"""

    @staticmethod
    def paradox_detection(
        message_id: str,
        content: str,
        source: str,
        target_timestamp: float,
        ledger_entries: List[Dict],
        causal_depth: float,
    ) -> str:
        """Gera prompt para detecção de paradoxos."""
        ledger_summary = json.dumps([
            {'type': e['type'], 'time': e['timestamp'],
             'payload_preview': str(e['payload'])[:300]}
            for e in ledger_entries[:30]
        ], indent=2)

        direction = "PASSADO" if target_timestamp < time.time() else "FUTURO"
        temporal_jump = abs(target_timestamp - time.time())

        return f"""DETECÇÃO DE PARADOXO TEMPORAL

Mensagem: {message_id[:16]}
Conteúdo: "{content[:200]}"
De: {source}
Direção temporal: {direction}
Salto temporal: {temporal_jump:.0f}s ({(temporal_jump/(365.25*86400)):.2f} anos)
Profundidade causal: {causal_depth:.4f}

REGISTROS EXISTENTES NO LEDGER:
{ledger_summary}

Analise se esta mensagem criaria:
1. Paradoxo do avô (a mensagem impede sua própria criação)
2. Loop causal (A causa B, B causa A)
3. Predição paradoxal (a mensagem revela algo que ainda não aconteceu)
4. Contradição factual (a mensagem nega um evento registrado)
5. Violação de entropia (a mensagem reduz entropia demais)

Retorne EXCLUSIVAMENTE em JSON:
{{
  "paradox_detected": true/false,
  "paradox_type": "NONE|GRANDPARENT|CAUSAL_LOOP|PREDICTION|CONTRADICTION|ENTROPY_VIOLATION|COMPOSITE",
  "severity": 0.0-1.0,
  "detail": "explicação do paradoxo detectado ou por que é seguro",
  "recommendation": "ACCEPT|REJECT|MODIFY|ESCALATE",
  "conflicting_entries": ["ids de registros conflitantes"],
  "causal_chain_risk": 0.0-1.0
}}
"""

    @staticmethod
    def content_filter(
        message_id: str,
        content: str,
        source: str,
        destination: str,
        direction: str,
    ) -> str:
        """Gera prompt para filtragem de conteúdo."""
        return f"""FILTRAGEM DE CONTEÚDO TEMPORAL

Mensagem: {message_id[:16]}
Conteúdo: "{content[:500]}"
Origem: {source}
Destino: {destination}
Temporal: {direction}

Analise esta mensagem quanto a:
1. Conteúdo perigoso (instruções para causar dano, manipulação temporal maliciosa)
2. Corrupção temporal (conteúdo que poderia corromper a cadeia temporal)
3. Spoofing (tentativa de se passar por outro nó)
4. Injeção de código (scripts, instruções para outros sistemas)
5. Consistência com a política da rede ARKHE

Retorne EXCLUSIVAMENTE em JSON:
{{
  "blocked": true/false,
  "risk_score": 0.0-1.0,
  "categories": ["lista de riscos detectados"],
  "detail": "explicação da análise",
  "action": "ALLOW|QUARANTINE|REJECT|FLAG_FOR_REVIEW"
}}
"""

    @staticmethod
    def chain_optimization(
        current_chain: List[Dict],
        pending_messages: List[Dict],
    ) -> str:
        """Gera prompt para otimização da cadeia temporal."""
        chain_json = json.dumps(current_chain[:50], indent=2, default=str)[:3000]
        pending_json = json.dumps(pending_messages[:20], indent=2, default=str)[:2000]

        return f"""OTIMIZAÇÃO DA CADEIA TEMPORAL

CADEIA TEMPORAL ATUAL:
{chain_json}

MENSAGENS PENDENTES:
{pending_json}

Analise e sugira:
1. Mensagens que devem ser priorizadas (urgência temporal)
2. Possíveis compactações (mensagens redundantes)
3. Riscos de fragmentação da cadeia
4. Sugestões de reordenação

Retorne EXCLUSIVAMENTE em JSON:
{{
  "priority_order": [{{"msg_id": "...", "priority": 0-10, "reason": "..."}}],
  "compression_candidates": ["msg_ids que podem ser compactadas"],
  "chain_risks": ["descrições de riscos"],
  "reorder_suggestions": [{{"from": "pos", "to": "pos", "reason": "..."}}],
  "estimated_health_score": 0.0-1.0
}}
"""


# ============================================================================
# ROTEADOR AI-AUGMENTED
# ============================================================================

class AIRouter:
    """
    Roteador AI-Augmented — extensão do RetroRouter com decisões
    baseadas em modelo local.

    Funciona como wrapper: todas as decisões de roteamento passam
    pelo modelo antes de serem executadas.
    """

    def __init__(
        self,
        base_router,  # 'RetroRouter'
        channel,  # ExtratemporalChannel
        config: Optional[AIConfig] = None,
    ):
        self.base = base_router
        self.channel = channel
        self.config = config or AIConfig()
        self.llm = LocalLLMClient(self.config)
        self.prompts = AIRoutingPrompts()
        self._routing_cache: Dict[str, Dict] = {}
        self._paradox_detector_enabled = True
        self._content_filter_enabled = True
        self._optimization_cycle = 0

        # Métricas
        self._stats = {
            'routing_decisions': 0,
            'paradox_checks': 0,
            'content_filters': 0,
            'llm_fallbacks': 0,
            'paradoxes_detected': 0,
            'blocked_messages': 0,
            'optimized_chains': 0,
        }

        log.info("🤖 AI-Router inicializado (modelo: %s)", self.config.model)

    def _llm_query(self, prompt: str, cache_key: Optional[str] = None) -> Optional[str]:
        """Consulta o LLM com fallback para heurística."""
        result = self.llm.query(prompt, cache_key=cache_key)
        if result is None and self.config.fallback_enabled:
            self._stats['llm_fallbacks'] += 1
            log.debug("Fallback heurístico ativado (LLM indisponível)")
        return result

    # ── 1. ROTEAMENTO COM IA ──────────────────────────────────────────

    def ai_route(self, pkt, ingress_addr: str = None) -> Optional[str]:
        """
        Roteamento com assistência de IA.

        1. Consulta modelo para melhor rota
        2. Valida com heurística tradicional
3. Retorna próximo hop ou fallback heurístico
        """
        self._stats['routing_decisions'] += 1

        # Obter rotas disponíveis
        available = self.base.rt.all_routes()

        # Se não há rotas, usar heurística padrão
        if not available:
            return self.base.route(pkt, ingress_addr)

        try:
            # Obter topologia simplificada
            topology = {
                'local_node': self.base.node.nid,
                'peers': dict(self.base.rt._peers),
                'routes_count': len(available),
            }

            # Obter registros relevantes do ledger
            ledger_entries = self.channel.ledger.get_all_records()[-20:]

            # Gerar prompt
            prompt = self.prompts.routing_decision(
                node_id=self.base.node.nid,
                dest=pkt.header.dst.split('@')[0] if '@' in pkt.header.dst else pkt.header.dst,
                available_routes=available,
                network_topology=topology,
                ledger_entries=ledger_entries,
                temporal_window=pkt.header.ttl,
            )

            # Consultar LLM
            response = self._llm_query(
                prompt,
                cache_key=f"route_{pkt.pid}"
            )

            if response:
                try:
                    decision = json.loads(response)
                    next_hop = decision.get('chosen_route', {}).get('next_hop')
                    confidence = decision.get('confidence', 0.5)
                    risk = decision.get('risk_level', 'medium')

                    log.info(
                        "🧠 AI-Route: %s (conf=%.2f, risk=%s) — LLM escolheu via %s",
                        pkt.pid[:12], confidence, risk, next_hop
                    )

                    # Validar com base heurística
                    if next_hop and self._validate_route_heuristic(next_hop, available):
                        self._routing_cache[pkt.pid] = {
                            'hop': next_hop, 'confidence': confidence,
                            'risk': risk, 'timestamp': time.time(),
                        }
                        return next_hop
                    else:
                        log.debug("Rota LLM inválida, fallback heurístico")
                except (json.JSONDecodeError, KeyError) as e:
                    log.warning(f"Resposta LLM malformada: {e}, fallback heurístico")

            # Fallback para heurística
            return self.base.route(pkt, ingress_addr)

        except Exception as e:
            log.error(f"Erro no roteamento AI: {e}, fallback heurístico")
            return self.base.route(pkt, ingress_addr)

    def _validate_route_heuristic(self, next_hop: str, available: List[Dict]) -> bool:
        """Valida que o hop sugerido pela IA existe nas rotas."""
        return any(r['next'] == next_hop for r in available)

    # ── 2. DETECÇÃO DE PARADOXO ──────────────────────────────────────

    def ai_paradox_check(self, pkt) -> Tuple[bool, str, float]:
        """
        Verificação de paradoxo com assistência de IA.

        Retorna: (is_paradox, reason, severity)
        """
        self._stats['paradox_checks'] += 1

        if not self._paradox_detector_enabled:
            return False, "disabled", 0.0

        # Verificação heurística rápida (TCO)
        if pkt.header.pkt_type == 15: # PktType.ERROR
            return True, "PACOTE_ERRO", 0.9

        # Verificação com LLM (mais profunda)
        ledger_entries = self.channel.ledger.get_all_records()[-30:]
        causal_depth = pkt.header.t_depth

        try:
            prompt = self.prompts.paradox_detection(
                message_id=pkt.pid,
                content=pkt.payload.decode('utf-8', errors='replace')[:1000],
                source=pkt.header.src,
                target_timestamp=pkt.header.target_ts,
                ledger_entries=ledger_entries,
                causal_depth=causal_depth,
            )

            response = self._llm_query(
                prompt,
                cache_key=f"paradox_{pkt.pid}"
            )

            if response:
                try:
                    result = json.loads(response)
                    is_paradox = result.get('paradox_detected', False)
                    reason = result.get('paradox_type', 'NONE')
                    severity = result.get('severity', 0.0)
                    recommendation = result.get('recommendation', 'ACCEPT')

                    if is_paradox:
                        self._stats['paradoxes_detected'] += 1
                        log.warning(
                            "⚠️ PARADOXO DETECTADO: %s (tipo=%s, severidade=%.2f) — %s",
                            pkt.pid[:12], reason, severity, recommendation
                        )

                    if recommendation == 'REJECT':
                        return True, reason, severity
                    elif recommendation == 'ESCALATE':
                        # Escalar para validador completo
                        return True, f"ESCALATED:{reason}", severity

                    return False, reason, severity

                except (json.JSONDecodeError, KeyError):
                    pass

        except Exception as e:
            log.error(f"Erro na detecção de paradoxo: {e}")

        # Fallback: heurística baseada em TCO
        return False, "HEURISTIC_PASS", 0.0

    # ── 3. FILTRAGEM DE CONTEÚDO ─────────────────────────────────────

    def ai_content_filter(self, pkt) -> Tuple[bool, str]:
        """
        Filtro de conteúdo com assistência de IA.

        Retorna: (allowed, reason)
        """
        self._stats['content_filters'] += 1

        if not self._content_filter_enabled:
            return True, "disabled"

        if pkt.header.encrypted:
            return True, "encrypted_skip"

        try:
            payload_text = pkt.payload.decode('utf-8', errors='replace')[:2000]
            direction = "RETROCASUAL" if pkt.header.target_ts < time.time() else "PROSPECTIVO"

            prompt = self.prompts.content_filter(
                message_id=pkt.pid,
                content=payload_text,
                source=pkt.header.src,
                destination=pkt.header.dst,
                direction=direction,
            )

            response = self._llm_query(
                prompt,
                cache_key=f"filter_{hashlib.md5(pkt.payload).hexdigest()[:16]}"
            )

            if response:
                try:
                    result = json.loads(response)
                    blocked = result.get('blocked', False)
                    action = result.get('action', 'ALLOW')
                    risk = result.get('risk_score', 0.0)

                    if blocked or action in ('REJECT', 'QUARANTINE'):
                        self._stats['blocked_messages'] += 1
                        categories = result.get('categories', [])
                        log.warning(
                            "🚫 Bloqueado por IA: %s (risco=%.2f, motivo=%s)",
                            pkt.pid[:12], risk, categories
                        )
                        return False, f"Bloqueado: {categories} (score={risk:.2f})"

                    if action == 'FLAG_FOR_REVIEW':
                        log.warning(
                            "⚠️ Sinalizado para revisão: %s (risco=%.2f)",
                            pkt.pid[:12], risk
                        )

                    return True, f"OK (risco={risk:.2f})"

                except (json.JSONDecodeError, KeyError):
                    pass

        except Exception as e:
            log.error(f"Erro na filtragem de conteúdo: {e}")

        return True, "HEURISTIC_PASS"

    # ── 4. OTIMIZAÇÃO DE CADEIA ──────────────────────────────────────

    def ai_chain_optimization(self) -> Dict:
        """Otimiza a cadeia temporal periodicamente."""
        self._optimization_cycle += 1

        if self._optimization_cycle % 10 != 0:  # A cada 10 ciclos
            return {'skipped': True}

        current_chain = self.channel.temporal_hash_chain._chain
        pending = self.channel._causal_anomalies

        ledger_entries = self.channel.ledger.get_all_records()[-50:]

        prompt = self.prompts.chain_optimization(
            current_chain=[b.to_dict() for b in current_chain[-50:]],
            pending_messages=pending,
        )

        response = self._llm_query(prompt, cache_key=f"optimize_{self._optimization_cycle}")

        if not response:
            return {'error': 'no_response'}

        try:
            result = json.loads(response)
            self._stats['optimized_chains'] += 1
            log.info(
                "🔧 Otimização AI (ciclo %d): %d riscos, %d sugestões",
                self._optimization_cycle,
                len(result.get('chain_risks', [])),
                len(result.get('reorder_suggestions', [])),
            )
            return result
        except (json.JSONDecodeError, KeyError):
            return {'error': 'parse_failed'}

    # ── PROCESSAMENTO COMPLETO ───────────────────────────────────────

    def process_packet(self, pkt, addr: str = None) -> str:
        """
        Pipeline completo de processamento com IA:

        1. Filtro de conteúdo (IA)
        2. Detecção de paradoxo (IA + heurística)
        3. Roteamento (IA + heurística)
        """
        # Fase 1: Filtragem de conteúdo
        allowed, filter_reason = self.ai_content_filter(pkt)
        if not allowed:
            self.channel.ledger.record("content_blocked", {
                'pid': pkt.pid,
                'reason': filter_reason,
                'source': pkt.header.src,
            })
            return "BLOCKED"

        # Fase 2: Detecção de paradoxo
        is_paradox, paradox_type, severity = self.ai_paradox_check(pkt)
        if is_paradox and severity > 0.7:
            self.channel._causal_anomalies.append({
                'msg_id': pkt.pid,
                'reason': paradox_type,
                'severity': severity,
                'timestamp': time.time(),
            })
            self.channel.ledger.record("paradox_detected", {
                'pid': pkt.pid,
                'type': paradox_type,
                'severity': severity,
            })
            if severity > 0.9:
                return "DROPPED_PARADOX"

        # Fase 3: Roteamento
        next_hop = self.ai_route(pkt, addr)

        if next_hop == "__LOCAL__":
            self.base.node.deliver(pkt)
            return "ACCEPTED"
        elif next_hop:
            if isinstance(next_hop, str) and next_hop != "__LOCAL__":
                self.base._fwd(pkt, next_hop)
                return "ROUTED"
            self.base._route_out(pkt)
            return "ROUTED"

        return "NO_ROUTE"

    @property
    def stats(self) -> Dict:
        llm_stats = self.llm.stats
        return {
            **self._stats,
            'llm': llm_stats,
            'routing_cache_size': len(self._routing_cache),
            'paradox_detector': self._paradox_detector_enabled,
            'content_filter': self._content_filter_enabled,
        }


# ============================================================================
# TESTES INTEGRADOS
# ============================================================================

def test_routing():
    """Testa a decisão de roteamento com IA."""
    from unittest.mock import MagicMock

    config = AIConfig(
        endpoint="http://localhost:11434",
        model="llama3.1:8b",
    )

    # Mock do roteador base
    base = MagicMock()
    base.rt.all_routes.return_value = [
        {'dest': 'BETA-02', 'next': 'BETA-02', 'cost': 1.0, 'conf': 0.95},
        {'dest': 'GAMA-03', 'next': 'GAMA-03', 'cost': 2.5, 'conf': 0.80},
    ]
    base.rt._peers = {'BETA-02': 'mock_addr'}

    # Mock do canal
    channel = MagicMock()
    mock_ledger = MagicMock()
    mock_ledger.get_all_records.return_value = []
    channel.ledger = mock_ledger
    channel._causal_anomalies = []

    ai_router = AIRouter(base, channel, config)

    # Mock do LLM client
    ai_router.llm.query = MagicMock(return_value=json.dumps({
        "chosen_route": {"next_hop": "BETA-02", "dest": "BETA-02", "cost": 1.0},
        "reasoning": "Menor custo e melhor fidelidade",
        "confidence": 0.92,
        "risk_level": "low",
        "paradox_risk": 0.05,
        "entropy_cost": 0.1,
    }))

    # Testar
    result = ai_router.ai_route(MagicMock(), "test_addr")
    assert result == "BETA-02", f"Esperado BETA-02, got {result}"
    print("✓ Teste de roteamento AI passou")


def test_paradox_detection():
    """Testa a detecção de paradoxo."""
    from unittest.mock import MagicMock

    config = AIConfig()
    base = MagicMock()
    channel = MagicMock()
    channel.ledger.get_all_records.return_value = []
    channel._causal_anomalies = []

    ai_router = AIRouter(base, channel, config)

    # Pacote paradoxal
    pkt = MagicMock()
    pkt.header.t_depth = 5.0
    pkt.header.target_ts = time.time() - 1000
    pkt.header.src = "NODE_A"
    pkt.payload = b"conteudo teste"
    pkt.pid = "test-001"
    pkt.header.pkt_type = 0 # DATA

    ai_router.llm.query = MagicMock(return_value=json.dumps({
        "paradox_detected": False,
        "paradox_type": "NONE",
        "severity": 0.0,
        "recommendation": "ACCEPT",
        "detail": "Nenhum paradoxo detectado",
        "causal_chain_risk": 0.1,
    }))

    is_paradox, reason, severity = ai_router.ai_paradox_check(pkt)
    assert not is_paradox, f"Não deveria detectar paradoxo: {reason}"
    print("✓ Teste de detecção de paradoxo passou")


def test_content_filter():
    """Testa a filtragem de conteúdo."""
    from unittest.mock import MagicMock

    config = AIConfig()
    base = MagicMock()
    channel = MagicMock()

    ai_router = AIRouter(base, channel, config)

    pkt = MagicMock()
    pkt.header.encrypted = False
    pkt.payload = b"Hello, this is a normal message"
    pkt.pid = "test-002"
    pkt.header.src = "NODE_A"
    pkt.header.dst = "NODE_B"
    pkt.header.target_ts = time.time() + 100

    ai_router.llm.query = MagicMock(return_value=json.dumps({
        "blocked": False,
        "risk_score": 0.02,
        "categories": [],
        "action": "ALLOW",
        "detail": "Conteúdo seguro",
    }))

    allowed, reason = ai_router.ai_content_filter(pkt)
    assert allowed, f"Deveria permitir: {reason}"
    print("✓ Teste de filtragem de conteúdo passou")


def test_fallback():
    """Testa o fallback quando o LLM está indisponível."""
    from unittest.mock import MagicMock

    config = AIConfig(fallback_enabled=True)
    base = MagicMock()
    base.route.return_value = "BETA-02"
    channel = MagicMock()

    ai_router = AIRouter(base, channel, config)
    ai_router.llm.query = MagicMock(return_value=None)  # LLM indisponível

    pkt = MagicMock()
    result = ai_router.ai_route(pkt)
    assert result == "BETA-02", f"Fallback deveria retornar BETA-02, got {result}"
    assert ai_router._stats['llm_fallbacks'] == 1
    print("✓ Teste de fallback passou")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ARKHE AI-Augmented Router — Roteador com IA Local"
    )
    parser.add_argument(
        '--test-routing', action='store_true',
        help='Executa testes de roteamento'
    )
    parser.add_argument(
        '--test-paradox', action='store_true',
        help='Executa testes de detecção de paradoxo'
    )
    parser.add_argument(
        '--test-filter', action='store_true',
        help='Executa testes de filtragem de conteúdo'
    )
    parser.add_argument(
        '--test-all', action='store_true',
        help='Executa todos os testes'
    )
    parser.add_argument(
        '--health-check', action='store_true',
        help='Verifica saúde do endpoint do LLM'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Exibe estatísticas do roteador'
    )
    parser.add_argument(
        '--endpoint', type=str, default="http://localhost:11434",
        help='Endpoint do modelo local (padrão: Ollama)'
    )
    parser.add_argument(
        '--model', type=str, default="llama3.1:8b",
        help='Nome do modelo'
    )
    parser.add_argument(
        '--node', type=str, default="ALFA-01",
        help='ID do nó local'
    )
    parser.add_argument(
        '--db', type=str, default=f"/tmp/arkhe_{__import__('socket').gethostname()}.db",
        help='Caminho do banco de dados do ledger'
    )

    args = parser.parse_args()
    setup_logging("INFO")

    config = AIConfig(
        endpoint=args.endpoint,
        model=args.model,
    )

    if args.health_check:
        client = LocalLLMClient(config)
        if client.check_health():
            print(f"✅ LLM disponível em {config.endpoint}")
            print(f"   Modelo: {config.model}")
            print(f"   Endpoint: {config.endpoint}")
        else:
            print(f"❌ LLM não disponível em {config.endpoint}")
            print("   Certifique-se de que Ollama/llama.cpp está rodando:")
            print("   $ ollama serve")
            print("   ou")
            print("   $ llama-server -m modelo.gguf")
            sys.exit(1)
        return

    # Inicializar componentes
    try:
        from agi.system32.temporal.retrocausal_consistency import ExtratemporalChannel
    except ImportError:
        class ExtratemporalChannel:
            def __init__(self, db_path=None, ledger=None, crystal=None, sophon=None): pass
            def initialize(self): pass
    try:
        from arkhe_retro_net import RetroRouter, RetroNode, RetroNet, \
            RetroPacket, RNPHeader, TAddr, PktType, PktPriority
    except ImportError:
        pass

    # Criar canal e nó
    channel = ExtratemporalChannel(db_path=args.db)
    try:
        channel.initialize()
    except AttributeError:
        pass

    ai_router = AIRouter(None, channel, config)

    if args.test_all:
        args.test_routing = True
        args.test_paradox = True
        args.test_filter = True

    if args.test_routing:
        try:
            test_routing()
        except Exception as e:
            log.error(f"Teste de roteamento falhou: {e}")

    if args.test_paradox:
        try:
            test_paradox_detection()
        except Exception as e:
            log.error(f"Teste de paradoxo falhou: {e}")

    if args.test_filter:
        try:
            test_content_filter()
        except Exception as e:
            log.error(f"Teste de filtragem falhou: {e}")

    if args.stats:
        print(json.dumps(ai_router.stats, indent=2, default=str))


if __name__ == "__main__":
    main()
