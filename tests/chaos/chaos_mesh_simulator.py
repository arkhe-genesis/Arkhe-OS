#!/usr/bin/env python3
"""
Substrato 9047‑B — Chaos Engineering para Broadcast Mesh
Simula 10.000 streams mock com falhas aleatórias (chaos monkeys)
para validar resiliência da malha em condições extremas.
"""

import asyncio, random, time, json, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ChaosAction(Enum):
    """Ações de caos que podem ser injetadas."""
    KILL_CONNECTOR = "kill_connector"         # Derruba um conector de plataforma
    SLOW_API = "slow_api"                     # Adiciona latência artificial na API
    CORRUPT_CREDENTIALS = "corrupt_creds"     # Invalida token OAuth2
    SPIKE_VIEWERS = "spike_viewers"           # Simula pico de viewers (ataque)
    DROP_MESSAGES = "drop_messages"           # Perde mensagens do chat
    KILL_SPARK_WORKER = "kill_spark_worker"   # Derruba worker Spark
    PARTITION_KAFKA = "partition_kafka"       # Causa rebalanceamento do Kafka
    FILL_DISK = "fill_disk"                   # Enche o disco de logs/métricas
    NETWORK_LATENCY = "network_latency"       # Adiciona latência de rede
    RANDOM_CRASH = "random_crash"             # Crash aleatório de qualquer serviço

@dataclass
class MockStream:
    """Stream simulado para teste de carga."""
    stream_id: str
    platform: str          # "twitch", "youtube", "tiktok"
    broadcaster_id: str
    base_viewers: int      # Número base de viewers (sem ataque)
    chat_rate_per_min: int # Mensagens de chat por minuto
    phi_c: float = 0.99
    active: bool = True

@dataclass
class ChaosEvent:
    """Evento de caos registrado."""
    event_id: str
    action: ChaosAction
    target: str
    timestamp: float
    duration_seconds: float
    impact: str            # "low", "medium", "high", "critical"
    recovered: bool = False

class ChaosBroadcastSimulator:
    """
    Simulador de 10.000 streams com chaos engineering.

    Funcionalidades:
    • Gera streams sintéticos com padrões realistas de audiência
    • Injeta falhas aleatórias (chaos monkeys) em intervalos configuráveis
    • Monitora recuperação automática da malha
    • Registra métricas de resiliência (MTTR, taxa de recuperação)
    • Gera relatório de chaos engineering para SRE
    """

    # Configurações de simulação
    NUM_STREAMS = 10000
    NUM_PLATFORMS = {"twitch": 5000, "youtube": 3000, "tiktok": 2000}
    CHAT_RATE_BASE = 50       # mensagens/minuto base
    VIEWER_BASE = 500         # viewers base

    # Configurações de caos
    CHAOS_INTERVAL_MIN = 30   # segundos entre eventos de caos
    CHAOS_INTERVAL_MAX = 120
    CHAOS_DURATION_MIN = 5    # duração mínima do caos
    CHAOS_DURATION_MAX = 60   # duração máxima

    # Distribuição de severidade dos eventos de caos
    CHAOS_SEVERITY_DIST = {
        "low": 0.50,      # 50% dos eventos são de baixo impacto
        "medium": 0.30,   # 30% médio
        "high": 0.15,     # 15% alto
        "critical": 0.05, # 5% crítico
    }

    def __init__(self, mesh_endpoint: str = "http://localhost:8053"):
        self.mesh_endpoint = mesh_endpoint
        self.streams: Dict[str, MockStream] = {}
        self.chaos_events: List[ChaosEvent] = []
        self.metrics = {
            "total_chaos_events": 0,
            "recovered_events": 0,
            "avg_recovery_time_seconds": 0.0,
            "max_recovery_time_seconds": 0.0,
            "streams_survived": 0,
            "streams_lost": 0,
        }
        self._running = False

    def generate_streams(self):
        """Gera 10.000 streams sintéticos com padrões realistas."""
        for platform, count in self.NUM_PLATFORMS.items():
            for i in range(count):
                stream_id = f"{platform}_stream_{i:05d}"

                # Distribuição Zipf para popularidade (poucos streams muito populares)
                popularity_rank = random.randint(1, count)
                base_viewers = int(self.VIEWER_BASE / (popularity_rank ** 0.5))

                # Variação por horário (simulada)
                hour_factor = 1.0 + 0.5 * (1 + (time.time() % 86400) / 43200)  # seno
                viewers = int(base_viewers * hour_factor)

                # Taxa de chat proporcional aos viewers
                chat_rate = int(self.CHAT_RATE_BASE * (viewers / self.VIEWER_BASE))

                stream = MockStream(
                    stream_id=stream_id,
                    platform=platform,
                    broadcaster_id=f"broadcaster_{random.randint(1, 100):04d}",
                    base_viewers=viewers,
                    chat_rate_per_min=chat_rate,
                    phi_c=0.99 + random.uniform(-0.01, 0.01),
                )
                self.streams[stream_id] = stream

        print(f"✅ {len(self.streams)} streams sintéticos gerados")
        print(f"   • Twitch: {self.NUM_PLATFORMS['twitch']}")
        print(f"   • YouTube: {self.NUM_PLATFORMS['youtube']}")
        print(f"   • TikTok: {self.NUM_PLATFORMS['tiktok']}")

    async def inject_chaos(self):
        """Loop de injeção de eventos de caos."""
        print("🐒 Chaos Monkey iniciado — injetando falhas aleatórias...")

        while self._running:
            # Aguardar intervalo aleatório
            await asyncio.sleep(random.randint(self.CHAOS_INTERVAL_MIN, self.CHAOS_INTERVAL_MAX))

            # Selecionar ação de caos
            action = random.choice(list(ChaosAction))

            # Selecionar alvo
            target = self._select_target(action)
            if not target:
                continue

            # Determinar severidade
            severity = self._select_severity()
            duration = random.randint(self.CHAOS_DURATION_MIN, self.CHAOS_DURATION_MAX)

            # Criar evento de caos
            event = ChaosEvent(
                event_id=hashlib.sha3_256(f"{action.value}:{target}:{time.time()}".encode()).hexdigest()[:12],
                action=action,
                target=target,
                timestamp=time.time(),
                duration_seconds=duration,
                impact=severity,
            )

            print(f"💥 Chaos: {action.value} → {target} (severity={severity}, duration={duration}s)")

            # Executar ação de caos
            await self._execute_chaos_action(event)

            # Registrar
            self.chaos_events.append(event)
            self.metrics["total_chaos_events"] += 1

            # Aguardar duração do caos
            await asyncio.sleep(duration)

            # Verificar recuperação
            recovered = await self._check_recovery(event)
            event.recovered = recovered

            if recovered:
                self.metrics["recovered_events"] += 1
                recovery_time = time.time() - event.timestamp
                self.metrics["avg_recovery_time_seconds"] = (
                    (self.metrics["avg_recovery_time_seconds"] * (self.metrics["recovered_events"] - 1) + recovery_time)
                    / self.metrics["recovered_events"]
                )
                self.metrics["max_recovery_time_seconds"] = max(
                    self.metrics["max_recovery_time_seconds"], recovery_time
                )
                print(f"   ✅ Recuperado em {recovery_time:.1f}s")
            else:
                print(f"   ❌ Não recuperado — requer intervenção manual")

    def _select_target(self, action: ChaosAction) -> Optional[str]:
        """Seleciona alvo apropriado para a ação de caos."""
        if action in [ChaosAction.KILL_CONNECTOR, ChaosAction.CORRUPT_CREDENTIALS,
                      ChaosAction.SLOW_API]:
            # Alvo: um conector de plataforma
            return random.choice(list(self.NUM_PLATFORMS.keys()))

        elif action == ChaosAction.SPIKE_VIEWERS:
            # Alvo: um stream aleatório
            return random.choice(list(self.streams.keys()))

        elif action in [ChaosAction.KILL_SPARK_WORKER, ChaosAction.PARTITION_KAFKA,
                        ChaosAction.FILL_DISK]:
            # Alvo: componente de infraestrutura
            return random.choice(["spark-worker-1", "spark-worker-2", "kafka-broker-1",
                                 "delta-lake", "temporal-chain"])

        elif action == ChaosAction.NETWORK_LATENCY:
            # Alvo: toda a malha
            return "mesh_network"

        elif action == ChaosAction.RANDOM_CRASH:
            # Qualquer coisa
            return random.choice(["mesh-orchestrator", "guardian", "spark-master",
                                 "kafka", "phi-bus", "temporal-chain"])

        return None

    def _select_severity(self) -> str:
        """Seleciona severidade baseada na distribuição configurada."""
        r = random.random()
        cumulative = 0.0
        for severity, prob in self.CHAOS_SEVERITY_DIST.items():
            cumulative += prob
            if r <= cumulative:
                return severity
        return "low"

    async def _execute_chaos_action(self, event: ChaosEvent):
        """Executa ação de caos específica (simulada)."""
        # Em produção: usar Chaos Mesh, LitmusChaos, ou API do Kubernetes

        if event.action == ChaosAction.KILL_CONNECTOR:
            # Simular: marcar streams da plataforma como offline
            platform = event.target
            for stream in self.streams.values():
                if stream.platform == platform:
                    stream.active = False
                    stream.phi_c -= 0.05

        elif event.action == ChaosAction.SPIKE_VIEWERS:
            # Simular: aumentar viewers drasticamente
            if event.target in self.streams:
                self.streams[event.target].base_viewers *= random.randint(50, 200)

        elif event.action == ChaosAction.KILL_SPARK_WORKER:
            # Simular: aumentar latência de processamento
            for stream in list(self.streams.values())[:1000]:
                stream.phi_c -= 0.02

        elif event.action == ChaosAction.RANDOM_CRASH:
            # Simular: queda geral de coerência
            for stream in self.streams.values():
                stream.phi_c -= random.uniform(0.01, 0.10)

        elif event.action == ChaosAction.NETWORK_LATENCY:
            # Simular: latência adicional
            for stream in self.streams.values():
                stream.phi_c -= 0.01

        # Ancorar evento de caos (simulado)
        print(f"   📊 Impacto: {sum(1 for s in self.streams.values() if not s.active)} streams offline, "
              f"Φ_C médio: {sum(s.phi_c for s in self.streams.values())/len(self.streams):.4f}")

    async def _check_recovery(self, event: ChaosEvent) -> bool:
        """Verifica se o sistema se recuperou do evento de caos."""
        # Simular: 85% de chance de recuperação automática
        recovered = random.random() < 0.85

        if recovered:
            # Restaurar streams afetados
            for stream in self.streams.values():
                if not stream.active and stream.platform == event.target:
                    stream.active = True
                    stream.phi_c = min(0.99, stream.phi_c + 0.05)

        return recovered

    async def run_simulation(self, duration_minutes: int = 60):
        """Executa simulação completa por N minutos."""
        print(f"\n🧪 Iniciando simulação de {self.NUM_STREAMS} streams por {duration_minutes} minutos...")
        print(f"🐒 Chaos Monkey ativo — {self.CHAOS_INTERVAL_MIN}s-{self.CHAOS_INTERVAL_MAX}s entre eventos\n")

        # Gerar streams
        self.generate_streams()

        self._running = True

        # Iniciar chaos monkey em background
        chaos_task = asyncio.create_task(self.inject_chaos())

        # Executar pelo tempo determinado
        await asyncio.sleep(duration_minutes * 60)

        # Parar chaos monkey
        self._running = False
        chaos_task.cancel()

        # Gerar relatório
        self._generate_report()

    def _generate_report(self):
        """Gera relatório de chaos engineering."""
        print("\n" + "=" * 70)
        print("📊 CHAOS ENGINEERING REPORT — 10K STREAMS SIMULATION")
        print("=" * 70)

        print(f"\n🔧 Chaos Events:")
        print(f"   • Total injetados: {self.metrics['total_chaos_events']}")
        print(f"   • Recuperados automaticamente: {self.metrics['recovered_events']}")
        print(f"   • Taxa de recuperação: {self.metrics['recovered_events']/max(1,self.metrics['total_chaos_events'])*100:.1f}%")
        print(f"   • MTTR médio: {self.metrics['avg_recovery_time_seconds']:.1f}s")
        print(f"   • Maior tempo de recuperação: {self.metrics['max_recovery_time_seconds']:.1f}s")

        print(f"\n📈 Streams:")
        active = sum(1 for s in self.streams.values() if s.active)
        print(f"   • Ativos: {active}/{len(self.streams)}")
        print(f"   • Perdidos: {len(self.streams) - active}")

        print(f"\n⚛️ Φ_C Final da Malha:")
        avg_phi = sum(s.phi_c for s in self.streams.values()) / len(self.streams)
        print(f"   • Média: {avg_phi:.4f}")

        print(f"\n🎯 Distribuição de Severidade:")
        for severity in ["low", "medium", "high", "critical"]:
            count = sum(1 for e in self.chaos_events if e.impact == severity)
            print(f"   • {severity}: {count}")

        print("\n✅ Simulação concluída. Relatório ancorado na TemporalChain (simulado).")

# Execução
if __name__ == "__main__":
    sim = ChaosBroadcastSimulator()
    # Usaremos uma duração menor para testes manuais rápidos
    asyncio.run(sim.run_simulation(duration_minutes=0.1))
