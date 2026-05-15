#!/usr/bin/env python3
"""Ferramentas MCP para a Malha de Transmissão Coerente."""
from typing import Dict, Any

from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh
from arkhe_twitch.twitch_connector import TwitchConfig
from arkhe_twitch.youtube_connector import YouTubeConfig
from arkhe_twitch.tiktok_connector import TikTokConfig

class Tool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

class TextContent:
    def __init__(self, type, text):
        self.type = type
        self.text = text

def register_mesh_tools(server: Any, mesh: CoherentBroadcastMesh):
    @server.list_tools()
    async def list_tools() -> list:
        return [
            Tool(
                name="mesh_status",
                description="Status completo da malha de transmissão coerente (todos os streams)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="mesh_add_stream",
                description="Adiciona um novo stream à malha coerente",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stream_id": {"type": "string"},
                        "platform": {"type": "string", "enum": ["twitch", "youtube", "tiktok"]},
                        "api_key": {"type": "string"},
                        "client_secret": {"type": "string"},
                        "channel_id": {"type": "string"},
                    },
                    "required": ["stream_id", "platform", "api_key", "channel_id"],
                },
            ),
            Tool(
                name="mesh_broadcast",
                description="Transmite mensagem para todos os streams da malha",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "source_stream": {"type": "string", "default": "system"},
                    },
                    "required": ["message"],
                },
            ),
            Tool(
                name="mesh_phi_c_snapshot",
                description="Snapshot da coerência Φ_C de todos os streams",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        if name == "mesh_status":
            status = mesh.get_mesh_status()
            return [TextContent(
                type="text",
                text=f"🌐 COHERENT BROADCAST MESH STATUS\n"
                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     f"📺 Streams: {status['active_streams']}/{status['total_streams']} ativos\n"
                     f"⚛️ Φ_C da malha: {status['mesh_phi_c']:.4f}\n"
                     f"👥 Total viewers: {status['total_viewers']}\n"
                     f"💬 Chat messages: {status['total_chat_messages']}\n"
                     f"🎁 Redemptions: {status['total_redemptions']}\n"
                     f"🎮 Drops: {status['total_drops']}\n"
            )]

        elif name == "mesh_add_stream":
            platform = arguments["platform"]

            if platform == "twitch":
                config = TwitchConfig(
                    client_id=arguments["api_key"],
                    client_secret=arguments.get("client_secret", ""),
                    broadcaster_id=arguments["channel_id"],
                )
            elif platform == "youtube":
                config = YouTubeConfig(
                    api_key=arguments["api_key"],
                    channel_id=arguments["channel_id"]
                )
            elif platform == "tiktok":
                config = TikTokConfig(
                    api_key=arguments["api_key"],
                    user_id=arguments["channel_id"]
                )
            else:
                raise ValueError(f"Platform {platform} not supported")

            await mesh.add_stream(arguments["stream_id"], platform, config)
            return [TextContent(
                type="text",
                text=f"✅ Stream '{arguments['stream_id']}' adicionado à malha. "
                     f"Total: {len(mesh.streams)} streams."
            )]

        elif name == "mesh_broadcast":
            await mesh._broadcast_to_mesh(arguments.get("source_stream", "system"), arguments["message"])
            return [TextContent(
                type="text",
                text=f"📡 Mensagem transmitida para {len(mesh.streams)} streams."
            )]

        elif name == "mesh_phi_c_snapshot":
            snapshots = {
                sid: f"Φ_C={s.phi_c:.4f} ({'🟢' if s.active else '🔴'}) [{s.platform}]"
                for sid, s in mesh.streams.items()
            }
            return [TextContent(
                type="text",
                text="⚛️ Φ_C SNAPSHOT:\n" + "\n".join(f"   {k}: {v}" for k, v in snapshots.items())
            )]

        raise ValueError(f"Unknown tool: {name}")
