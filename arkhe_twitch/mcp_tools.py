#!/usr/bin/env python3
"""Ferramentas MCP para integração ARKHE + Twitch.tv"""

class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

class Tool:
    def __init__(self, name: str, description: str, inputSchema: dict):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

def register_twitch_tools(server, twitch_connector):
    @server.list_tools()
    async def list_tools() -> list:
        return [
            Tool(
                name="twitch_stream_info",
                description="Obtém informações do stream atual (título, viewers, jogo, Φ_C)",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="twitch_send_chat",
                description="Envia mensagem no chat com validação Guardian",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Mensagem a enviar"},
                        "reply_to": {"type": "string", "description": "ID da mensagem para reply (opcional)"},
                    },
                    "required": ["message"],
                },
            ),
            Tool(
                name="twitch_update_title",
                description="Atualiza título do stream",
                inputSchema={
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                },
            ),
            Tool(
                name="twitch_create_reward",
                description="Cria recompensa customizada de Channel Points",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "cost": {"type": "integer"},
                        "prompt": {"type": "string"},
                        "color": {"type": "string", "default": "#00FF00"},
                    },
                    "required": ["title", "cost"],
                },
            ),
            Tool(
                name="twitch_get_redemptions",
                description="Obtém redemptions pendentes de uma recompensa",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reward_id": {"type": "string"},
                        "status": {"type": "string", "default": "UNFULFILLED"},
                    },
                    "required": ["reward_id"],
                },
            ),
            Tool(
                name="twitch_fulfill_redemption",
                description="Marca redemption como fulfilled",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "redemption_id": {"type": "string"},
                        "reward_id": {"type": "string"},
                    },
                    "required": ["redemption_id", "reward_id"],
                },
            ),
            Tool(
                name="twitch_start_commercial",
                description="Inicia comercial no stream",
                inputSchema={
                    "type": "object",
                    "properties": {"length": {"type": "integer", "default": 60}},
                    "required": [],
                },
            ),
            Tool(
                name="twitch_phi_c",
                description="Verifica Φ_C do stream atual",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="twitch_metrics",
                description="Obtém métricas Prometheus do conector",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="twitch_health",
                description="Health check do conector Twitch",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        tc = twitch_connector

        if name == "twitch_stream_info":
            stream = await tc.get_stream_info()
            if stream:
                return [TextContent(
                    type="text",
                    text=f"📺 {stream.broadcaster_name} — {stream.title}\n"
                         f"🎮 {stream.game_name} | 👥 {stream.viewer_count} viewers\n"
                         f"🌐 {stream.language} | 🔞 Mature: {stream.is_mature}\n"
                         f"⚛️ Φ_C: {stream.phi_c_coherence:.4f} | 🔐 Seal: {stream.temporal_seal or 'N/A'}"
                )]
            return [TextContent(type="text", text="❌ Stream offline ou não encontrado")]

        elif name == "twitch_send_chat":
            success = await tc.send_chat_message(arguments["message"], arguments.get("reply_to"))
            return [TextContent(
                type="text",
                text=f"{'✅' if success else '❌'} Mensagem enviada" if success else "❌ Bloqueada pelo Guardian ou erro na API"
            )]

        elif name == "twitch_update_title":
            success = await tc.update_stream_title(arguments["title"])
            return [TextContent(type="text", text=f"{'✅' if success else '❌'} Título atualizado")]

        elif name == "twitch_create_reward":
            reward_id = await tc.create_custom_reward(
                arguments["title"], arguments["cost"],
                arguments.get("prompt", ""), arguments.get("color", "#00FF00")
            )
            return [TextContent(
                type="text",
                text=f"{'✅' if reward_id else '❌'} Reward criado: {reward_id or 'falhou'}"
            )]

        elif name == "twitch_get_redemptions":
            redemptions = await tc.get_redemptions(arguments["reward_id"], arguments.get("status", "UNFULFILLED"))
            if not redemptions:
                return [TextContent(type="text", text="📭 Nenhuma redemption pendente")]
            return [TextContent(
                type="text",
                text="\n".join(
                    f"[{r.status}] {r.user_name}: {r.reward_title} ({r.reward_cost} pts) — {r.user_input[:50]}"
                    for r in redemptions[:10]
                )
            )]

        elif name == "twitch_fulfill_redemption":
            success = await tc.fulfill_redemption(arguments["redemption_id"], arguments["reward_id"])
            return [TextContent(type="text", text=f"{'✅' if success else '❌'} Redemption fulfilled")]

        elif name == "twitch_start_commercial":
            result = await tc._api_request(
                "POST", f"/channels/commercial",
                json={"broadcaster_id": tc.config.broadcaster_id, "length": arguments.get("length", 60)}
            )
            success = "error" not in result
            return [TextContent(type="text", text=f"{'✅' if success else '❌'} Comercial iniciado")]

        elif name == "twitch_phi_c":
            phi = tc.phi_bus.get_mesh_coherence() if tc.phi_bus else 0.997
            return [TextContent(type="text", text=f"⚛️ Φ_C do stream: {phi:.4f}")]

        elif name == "twitch_metrics":
            metrics = tc.get_prometheus_metrics()
            return [TextContent(type="text", text=f"```prometheus\n{metrics}\n```")]

        elif name == "twitch_health":
            health = await tc.health_check()
            return [TextContent(
                type="text",
                text=f"{'🟢' if health['status'] == 'healthy' else '🔴'} {health['status']}\n"
                     f"Authenticated: {health['authenticated']}\n"
                     f"EventSub: {health['eventsub_connected']}\n"
                     f"Chat history: {health['chat_history_size']}\n"
                     f"API requests: {health['metrics']['api_requests']}"
            )]

        raise ValueError(f"Unknown tool: {name}")
