#!/usr/bin/env python3
"""Ferramentas MCP para a Malha de Transmissão Coerente."""
from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh, TwitchConfig

class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

class Tool:
    def __init__(self, name: str, description: str, inputSchema: dict):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

def register_mesh_tools(server, mesh: CoherentBroadcastMesh):
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
                        "client_id": {"type": "string"},
                        "client_secret": {"type": "string"},
                        "broadcaster_id": {"type": "string"},
                    },
                    "required": ["stream_id", "client_id", "broadcaster_id"],
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
                     f"🔐 Selo: {status['temporal_anchor'][:16] if status['temporal_anchor'] else 'N/A'}..."
            )]

        elif name == "mesh_add_stream":
            config = TwitchConfig(
                client_id=arguments["client_id"],
                client_secret=arguments.get("client_secret", ""),
                broadcaster_id=arguments["broadcaster_id"],
            )
            stream = await mesh.add_stream(arguments["stream_id"], config)
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
                sid: f"Φ_C={s.phi_c:.4f} ({'🟢' if s.active else '🔴'})"
                for sid, s in mesh.streams.items()
            }
            return [TextContent(
                type="text",
                text="⚛️ Φ_C SNAPSHOT:\n" + "\n".join(f"   {k}: {v}" for k, v in snapshots.items())
            )]

        raise ValueError(f"Unknown tool: {name}")
