#!/usr/bin/env python3
"""
launch_broadcast_mesh.py — Ativação do modo broadcast full.
Carrega credenciais reais de vault/variáveis de ambiente, conecta a Twitch,
YouTube e TikTok, inicia o processamento Spark e expõe MCP.
"""

import asyncio, os, json, logging
from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh
from arkhe_broadcast.youtube_live_connector import YouTubeLiveConnector, YouTubeConfig
from arkhe_broadcast.tiktok_live_connector import TikTokLiveConnector, TikTokConfig
from arkhe_broadcast.twitch_connector import ArkheTwitchConnector, TwitchConfig
from arkhe_spark.spark_distributed_processor import DistributedChatProcessor
from arkhe_mcp.server import ArkheMCPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    return {
        "twitch": {
            "streamer_01": TwitchConfig(
                client_id=os.environ["TWITCH_CLIENT_ID"],
                client_secret=os.environ["TWITCH_CLIENT_SECRET"],
                broadcaster_id=os.environ["TWITCH_BROADCASTER_ID"],
            ),
        },
        "youtube": {
            "channel_01": YouTubeConfig(
                client_id=os.environ["YT_CLIENT_ID"],
                client_secret=os.environ["YT_CLIENT_SECRET"],
                refresh_token=os.environ["YT_REFRESH_TOKEN"],
                channel_id=os.environ["YT_CHANNEL_ID"],
                api_key=os.environ["YT_API_KEY"],
            ),
        },
        "tiktok": {
            "room_01": TikTokConfig(
                client_key=os.environ["TIKTOK_CLIENT_KEY"],
                client_secret=os.environ["TIKTOK_CLIENT_SECRET"],
                access_token=os.environ["TIKTOK_ACCESS_TOKEN"],
                open_id=os.environ["TIKTOK_OPEN_ID"],
                room_id=os.environ.get("TIKTOK_ROOM_ID"),
            ),
        },
    }

async def main():
    logger.info("🚀 Iniciando ARKHE Full Broadcast Mode...")

    # 1. Inicializar serviços core
    from arkhe_timechain.temporal_chain import TemporalChain
    from arkhe_phi.phi_bus import PhiCSyncBusOmegaV2
    from arkhe_security.guardian_attractor import GuardianAttractor

    temporal = TemporalChain(storage_backend="postgresql")
    phi_bus = PhiCSyncBusOmegaV2(target_phi_c=1.0)
    guardian = GuardianAttractor(vocab_size=50000, embed_dim=128)

    # 2. Carregar configurações de credenciais (vault/env)
    config = load_config()

    # 3. Criar orquestrador multi‑plataforma
    mesh = CoherentBroadcastMesh(phi_bus=phi_bus, temporal_chain=temporal)

    # Adicionar streams Twitch
    for name, tw_cfg in config["twitch"].items():
        conn = ArkheTwitchConnector(tw_cfg, temporal, guardian, phi_bus)
        await conn.__aenter__()
        # Autenticar com OAuth2 (código já implementado no conector)
        # Em produção: usar tokens pré‑obtidos
        await mesh.add_stream(f"twitch_{name}", conn)

    # Adicionar streams YouTube
    for name, yt_cfg in config["youtube"].items():
        conn = YouTubeLiveConnector(yt_cfg, temporal, guardian, phi_bus)
        mesh.connectors[f"youtube_{name}"] = conn
        await conn.subscribe_events(lambda msg: mesh._handle_message(name, msg))

    # Adicionar streams TikTok
    for name, tk_cfg in config["tiktok"].items():
        conn = TikTokLiveConnector(tk_cfg, temporal, guardian, phi_bus)
        mesh.connectors[f"tiktok_{name}"] = conn
        await conn.subscribe_events(lambda msg: mesh._handle_message(name, msg))

    # 4. Iniciar processamento Spark distribuído
    spark_processor = DistributedChatProcessor(
        kafka_broker=os.environ.get("KAFKA_BROKER", "kafka.arkhe:9092"),
        guardian_endpoint=os.environ.get("GUARDIAN_ENDPOINT", "http://guardian:8050"),
    )
    spark_query = spark_processor.start_processing()

    # 5. Iniciar monitoramento da malha
    await mesh.start_mesh_monitoring()

    # 6. Expor ferramentas MCP
    mcp = ArkheMCPServer()
    from arkhe_broadcast.mesh_mcp_tools import register_mesh_tools
    register_mesh_tools(mcp, mesh)

    # Health check endpoint
    logger.info("✅ Modo broadcast full ativado.")
    logger.info("   • Twitch: %d stream(s)", len(config["twitch"]))
    logger.info("   • YouTube: %d stream(s)", len(config["youtube"]))
    logger.info("   • TikTok: %d stream(s)", len(config["tiktok"]))
    logger.info("   • Spark: processamento em lote ativo")
    logger.info("   • MCP: ferramentas expostas na porta 8053")

    # Manter execução
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
