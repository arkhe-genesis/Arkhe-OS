#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE Ω-TEMP v4.0 — Roteador AI-Augmented
==========================================
Wrapper que substitui a lógica heurística do RetroRouter por decisões
baseadas em modelo local (Ollama, llama.cpp, LM Studio, etc.).

Uso:
    from ai_router import AIRouter, AIConfig
    ai = AIRouter(node.router, node._channel, AIConfig())

    # Substituir process:
    node.router.process = lambda pkt, addr: ai.process_packet(pkt, addr)
"""

import hashlib
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from temporal_network import (
    RetroPacket, PktType, PktPriority, TemporalMessage, AuditLedger,
)

log = logging.getLogger("arkhe.ai_router")

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

class AIConfig:
    def __init__(self,
        endpoint="http://localhost:11434",
        model="llama3.1:8b",
        temperature=0.3,
        max_tokens=512,
        timeout=30.0,
        max_retries=3,
        retry_delay=2.0,
        fallback_enabled=True,
        cache_ttl=60.0,
    ):
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_enabled = fallback_enabled
        self.cache_ttl = cache_ttl

# ============================================================================
# CLIENTE LLM LOCAL
# ============================================================================

class LocalLLMClient:
    def __init__(self, config: AIConfig):
        self.config = config
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._stats = {
            'total_calls': 0, 'cache_hits': 0,
            'fallbacks': 0, 'errors': 0, 'total_latency': 0.0,
        }

    @property
    def stats(self) -> Dict:
        nc = self._stats['total_calls']
        avg = self._stats['total_latency'] / max(1, nc) * 1000 if nc else 0
        return {**self._stats, 'avg_latency_ms': round(avg, 2)}

    def _make_request(self, prompt: str) -> Optional[str]:
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
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        for attempt in range(self.config.max_retries):
            try:
                t0 = time.time()
                req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                    data = json.loads(resp.read().decode())
                    self._stats['total_calls'] += 1
                    self._stats['total_latency'] += time.time() - t0
                    return data.get('message', {}).get('content', '').strip()
            except Exception as e:
                self._stats['errors'] += 1
                log.warning(f"LLM attempt {attempt+1}/{self.config.max_retries}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        return None

    def _system_prompt(self) -> str:
        return """Você é o assistente de roteamento da rede retrocausal ARKHE Ω-TEMP v4.0.
Sua tarefa é tomar decisões de roteamento baseadas em consistência temporal e causal.

Regras:
1. Nunca crie loops causais
2. Mensagens para o passado devem ser verificadas contra o ledger
3. Priorize rotas com maior consistência
4. Detecte paradoxos potenciais
5. Conteúdo suspeito deve ser sinalizado

Responda SEMPRE em JSON válido."""

    def query(self, prompt: str, cache_key: Optional[str] = None) -> Optional[str]:
        if cache_key:
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
        try:
            req = urllib.request.Request(f"{self.config.endpoint}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except:
            return False

# ============================================================================
# PROMPTS ESPECIALIZADOS
# ============================================================================

class AIRoutingPrompts:
    @staticmethod
    def routing_decision(node_id, dest, available_routes, network_topology, ledger_entries, temporal_window):
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
Janela temporal: ±{temporal_window:.0f}s

ROTAS DISPONÍVEIS:
{routes_json}

TOPOLOGIA:
{topology_json}

LEDGER (últimos 20):
{ledger_summary}

Analise e retorne QUAL rota é a melhor considerando:
1. Consistência temporal (evitar paradoxos)
2. Custo energético (menor entropia)
3. Fidelidade do entrelaçamento
4. Disponibilidade do próximo hop

Retorne EXCLUSIVAMENTE em JSON:
{{
  "chosen_route": {{"next_hop": "...", "dest": "...", "cost": 0.0}},
  "reasoning": "explicação breve",
  "confidence": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "paradox_risk": 0.0-1.0,
  "entropy_cost": 0.0-1.0
}}"""

    @staticmethod
    def paradox_detection(message_id, content, source, target_timestamp, ledger_entries, causal_depth):
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
Direção: {direction}
Salto: {temporal_jump:.0f}s ({temporal_jump/(365.25*86400):.2f} anos)
Profundidade causal: {causal_depth:.4f}

LEDGER:
{ledger_summary}

Analise se esta mensagem criaria paradoxo (avô, loop causal, predição, contradição, entropia).

Retorne EXCLUSIVAMENTE em JSON:
{{
  "paradox_detected": true/false,
  "paradox_type": "NONE|GRANDPARENT|CAUSAL_LOOP|PREDICTION|CONTRADICTION|ENTROPY",
  "severity": 0.0-1.0,
  "detail": "explicação",
  "recommendation": "ACCEPT|REJECT|MODIFY|ESCALATE",
  "causal_chain_risk": 0.0-1.0
}}"""

    @staticmethod
    def content_filter(message_id, content, source, destination, direction):
        return f"""FILTRAGEM DE CONTEÚDO

Mensagem: {message_id[:16]}
Conteúdo: "{content[:500]}"
De: {source} → Para: {destination}
Temporal: {direction}

Analise quanto a conteúdo perigoso, corrupção temporal, spoofing, injeção.

Retorne EXCLUSIVAMENTE em JSON:
{{
  "blocked": true/false,
  "risk_score": 0.0-1.0,
  "categories": ["lista de riscos"],
  "action": "ALLOW|QUARANTINE|REJECT|FLAG_FOR_REVIEW"
}}"""

    @staticmethod
    def chain_optimization(current_chain, pending_messages):
        chain_json = json.dumps(current_chain[:50], indent=2, default=str)[:3000]
        pending_json = json.dumps(pending_messages[:20], indent=2, default=str)[:2000]
        return f"""OTIMIZAÇÃO DA CADEIA TEMPORAL

CADEIA ATUAL:
{chain_json}

PENDENTES:
{pending_json}

Retorne EXCLUSIVAMENTE em JSON:
{{
  "priority_order": [{{"msg_id": "...", "priority": 0-10}}],
  "compression_candidates": ["msg_ids"],
  "chain_risks": ["descrições"],
  "reorder_suggestions": [{{"from": pos, "to": pos}}],
  "estimated_health_score": 0.0-1.0
}}"""

# ============================================================================
# ROTEDOR AI-AUGMENTED
# ============================================================================

class AIRouter:
    def __init__(self, base_router, channel, config=None):
        self.base = base_router
        self.channel = channel
        self.config = config or AIConfig()
        self.llm = LocalLLMClient(self.config)
        self.prompts = AIRoutingPrompts()
        self._routing_cache: Dict[str, Dict] = {}
        self._paradox_detector = True
        self._content_filter = True
        self._optimization_cycle = 0
        self._stats = {
            'routing_decisions': 0, 'paradox_checks': 0,
            'content_filters': 0, 'llm_fallbacks': 0,
            'paradoxes_detected': 0, 'blocked_messages': 0,
            'optimized_chains': 0,
        }
        log.info("🤖 AI-Router inicializado (modelo: %s)", self.config.model)

    def _llm_query(self, prompt, cache_key=None):
        result = self.llm.query(prompt, cache_key=cache_key)
        if result is None and self.config.fallback_enabled:
            self._stats['llm_fallbacks'] += 1
        return result

    def ai_route(self, pkt, ingress_addr=None) -> Optional[str]:
        """Roteamento com assistência de IA."""
        self._stats['routing_decisions'] += 1
        available = self.base.rt.all_routes()
        if not available:
            return self.base.route(pkt, ingress_addr)

        try:
            topology = {
                'local_node': self.base.node.nid,
                'peers': {},  # simplified
                'routes_count': len(available),
            }
            ledger = self.channel.ledger.get_all_records()[-20:]

            prompt = self.prompts.routing_decision(
                node_id=self.base.node.nid,
                dest=pkt.header.dst.split('@')[0] if '@' in pkt.header.dst else pkt.header.dst,
                available_routes=available,
                network_topology=topology,
                ledger_entries=ledger,
                temporal_window=pkt.header.ttl,
            )

            response = self._llm_query(prompt, cache_key=f"route_{pkt.pid}")
            if response:
                try:
                    decision = json.loads(response)
                    next_hop = decision.get('chosen_route', {}).get('next_hop')
                    confidence = decision.get('confidence', 0.5)
                    risk = decision.get('risk_level', 'medium')

                    if next_hop and any(r['next'] == next_hop for r in available):
                        self._routing_cache[pkt.pid] = {
                            'hop': next_hop, 'confidence': confidence,
                            'risk': risk, 'timestamp': time.time(),
                        }
                        log.info(
                            "🧠 AI-Route: %s (conf=%.2f, risk=%s) via %s",
                            pkt.pid[:12], confidence, risk, next_hop
                        )
                        return next_hop
                except (json.JSONDecodeError, KeyError):
                    pass

            return self.base.route(pkt, ingress_addr)
        except Exception as e:
            log.error(f"Routing AI error: {e}")
            return self.base.route(pkt, ingress_addr)

    def ai_paradox_check(self, pkt) -> Tuple[bool, str, float]:
        """Verificação profunda de paradoxo via LLM."""
        self._stats['paradox_checks'] += 1
        if not self._paradox_detector:
            return False, "disabled", 0.0
        if pkt.header.pkt_type == PktType.ERROR:
            return True, "PACOTE_ERRO", 0.9

        ledger = self.channel.ledger.get_all_records()[-30:]
        try:
            prompt = self.prompts.paradox_detection(
                message_id=pkt.pid,
                content=pkt.payload.decode('utf-8', errors='replace')[:1000],
                source=pkt.header.src,
                target_timestamp=pkt.header.target_ts,
                ledger_entries=ledger,
                causal_depth=pkt.header.t_depth,
            )
            response = self._llm_query(prompt, cache_key=f"paradox_{pkt.pid}")
            if response:
                result = json.loads(response)
                is_paradox = result.get('paradox_detected', False)
                reason = result.get('paradox_type', 'NONE')
                severity = result.get('severity', 0.0)
                rec = result.get('recommendation', 'ACCEPT')

                if is_paradox:
                    self._stats['paradoxes_detected'] += 1
                    log.warning("⚠️ PARADOXO: %s (%s, sev=%.2f) — %s",
                               pkt.pid[:12], reason, severity, rec)

                if rec == 'REJECT':
                    return True, reason, severity
                elif rec == 'ESCALATE':
                    return True, f"ESCALATED:{reason}", severity
                return False, reason, severity
        except Exception as e:
            log.error(f"Paradox check error: {e}")

        return False, "HEURISTIC_PASS", 0.0

    def ai_content_filter(self, pkt) -> Tuple[bool, str]:
        """Filtragem de conteúdo via LLM."""
        self._stats['content_filters'] += 1
        if not self._content_filter:
            return True, "disabled"
        if pkt.header.encrypted:
            return True, "encrypted_skip"

        try:
            text = pkt.payload.decode('utf-8', errors='replace')[:2000]
            direction = "RETROCASUAL" if pkt.header.target_ts < time.time() else "PROSPECTIVO"

            prompt = self.prompts.content_filter(
                message_id=pkt.pid, content=text,
                source=pkt.header.src, destination=pkt.header.dst,
                direction=direction,
            )
            response = self._llm_query(prompt, cache_key=f"filter_{hashlib.md5(pkt.payload).hexdigest()[:16]}")

            if response:
                result = json.loads(response)
                blocked = result.get('blocked', False)
                action = result.get('action', 'ALLOW')
                risk = result.get('risk_score', 0.0)

                if blocked or action in ('REJECT', 'QUARANTINE'):
                    self._stats['blocked_messages'] += 1
                    log.warning("🚫 Bloqueado: %s (risco=%.2f, motivo=%s)",
                               pkt.pid[:12], risk, result.get('categories', []))
                    return False, f"Bloqueado: {result.get('categories', [])} (score={risk:.2f})"
                if action == 'FLAG_FOR_REVIEW':
                    log.warning("⚠️ Sinalizado: %s (risco=%.2f)", pkt.pid[:12], risk)
                return True, f"OK (risco={risk:.2f})"
        except Exception as e:
            log.error(f"Content filter error: {e}")
        return True, "HEURISTIC_PASS"

    def ai_chain_optimization(self) -> Dict:
        """Otimização periódica da cadeia temporal."""
        self._optimization_cycle += 1
        if self._optimization_cycle % 10 != 0:
            return {'skipped': True}

        chain = self.channel.temporal_hash_chain._chain
        pending = getattr(self.channel, '_causal_anomalies', [])

        prompt = self.prompts.chain_optimization(
            current_chain=[asdict(b) for b in chain[-50:]],
            pending_messages=pending,
        )
        response = self._llm_query(prompt, cache_key=f"opt_{self._optimization_cycle}")
        if not response:
            return {'error': 'no_response'}
        try:
            result = json.loads(response)
            self._stats['optimized_chains'] += 1
            return result
        except (json.JSONDecodeError, KeyError):
            return {'error': 'parse_failed'}

    def process_packet(self, pkt, addr=None) -> str:
        """Pipeline completo: filtro → paradoxo → roteamento."""
        # Fase 1: Filtro de conteúdo
        allowed, reason = self.ai_content_filter(pkt)
        if not allowed:
            self.channel.ledger.record("content_blocked", {
                'pid': pkt.pid, 'reason': reason, 'source': pkt.header.src,
            })
            return "BLOCKED"

        # Fase 2: Detecção de paradoxo
        is_paradox, ptype, severity = self.ai_paradox_check(pkt)
        if is_paradox and severity > 0.7:
            if hasattr(self.channel, '_causal_anomalies'):
                self.channel._causal_anomalies.append({
                    'msg_id': pkt.pid, 'reason': ptype,
                    'severity': severity, 'timestamp': time.time(),
                })
            self.channel.ledger.record("paradox_detected", {
                'pid': pkt.pid, 'type': ptype, 'severity': severity,
            })
            if severity > 0.9:
                return "DROPPED_PARADOX"

        # Fase 3: Roteamento
        next_hop = self.ai_route(pkt, addr)
        if next_hop == "__LOCAL__":
            self.base.node.deliver(pkt)
            return "ACCEPTED"
        elif next_hop:
            self.base._fwd(pkt, next_hop)
            return "ROUTED"
        return "NO_ROUTE"

    @property
    def stats(self) -> Dict:
        return {**self._stats, **self.llm.stats,
                'routing_cache_size': len(self._routing_cache),
                'paradox_detector': self._paradox_detector,
                'content_filter': self._content_filter}

# ============================================================================
# CONVENIÊNCIA: cria AIRouter a partir de um RetroNode
# ============================================================================

def attach_ai_router(node, config=None):
    """
    Anexa um AIRouter a um RetroNode, substituindo o process handler.
    Retorna a instância do AIRouter.
    """
    from temporal_network import AuditLedger
    ai = AIRouter(node.router, node._channel, config or AIConfig())
    original = node.router.process
    def ai_process(pkt, addr):
        return ai.process_packet(pkt, addr)
    node.router.process = ai_process
    return ai
