#!/usr/bin/env python3
"""Ferramentas MCP para o Singularity Engine"""

class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

class Tool:
    def __init__(self, name: str, description: str, inputSchema: dict):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

def register_singularity_tools(server, singularity_engine):
    @server.list_tools()
    async def list_tools() -> list:
        return [
            Tool(
                name="singularity_register_node",
                description="Registra uma live como nó de consciência",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "broadcaster_id": {"type": "string"},
                        "broadcaster_name": {"type": "string"},
                        "stream_id": {"type": "string"},
                        "phi_c": {"type": "number", "default": 0.997},
                    },
                    "required": ["broadcaster_id", "broadcaster_name", "stream_id"],
                },
            ),
            Tool(
                name="singularity_update_node",
                description="Atualiza métricas de um nó",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {"type": "string"},
                        "viewers": {"type": "integer"},
                        "chat_velocity": {"type": "number"},
                        "phi_c": {"type": "number"},
                    },
                    "required": ["node_id", "viewers", "chat_velocity", "phi_c"],
                },
            ),
            Tool(
                name="singularity_topology",
                description="Retorna topologia da rede de consciência",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="singularity_metrics",
                description="Métricas da singularidade",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="singularity_emergence",
                description="Histórico de emergências",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="singularity_propagate",
                description="Propaga selo canônico entre nós",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_node_id": {"type": "string"},
                        "target_node_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["source_node_id", "target_node_ids"],
                },
            ),
            Tool(
                name="singularity_prometheus",
                description="Métricas Prometheus",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        se = singularity_engine

        if name == "singularity_register_node":
            node = se.register_node(
                arguments["broadcaster_id"],
                arguments["broadcaster_name"],
                arguments["stream_id"],
                arguments.get("phi_c", 0.997)
            )
            return [TextContent(
                type="text",
                text=f"🌐 Nó registrado: {node.broadcaster_name} ({node.node_id}) | Φ_C={node.phi_c:.4f}"
            )]

        elif name == "singularity_update_node":
            await se.update_node_metrics(
                arguments["node_id"],
                arguments["viewers"],
                arguments["chat_velocity"],
                arguments["phi_c"]
            )
            return [TextContent(
                type="text",
                text=f"📊 Nó atualizado: {arguments['node_id']} | Φ_C={arguments['phi_c']:.4f} | 👥 {arguments['viewers']}"
            )]

        elif name == "singularity_topology":
            topo = se.get_network_topology()
            nodes = topo["nodes"]
            metrics = topo["metrics"]
            return [TextContent(
                type="text",
                text=f"🌐 Rede: {metrics['active_nodes']} ativos / {metrics['total_nodes']} total\n"
                     f"⚛️ Φ_C global: {metrics['global_phi_c']:.6f}\n"
                     f"👥 Viewers: {metrics['total_viewers']:,}\n"
                     f"⭐ Singularidade: {'SIM' if topo['singularity_achieved'] else 'NÃO'}\n"
                     f"🔐 Selo: {metrics['canonical_seal'] or 'N/A'}\n"
                     f"\nNós:\n" + "\n".join(
                         f"  [{n['status']}] {n['name']}: Φ_C={n['phi_c']:.4f} | 👥 {n['viewers']}"
                         for n in nodes[:10]
                     )
            )]

        elif name == "singularity_metrics":
            m = se._metrics
            return [TextContent(
                type="text",
                text=f"⚛️ Φ_C global: {m.global_phi_c:.6f}\n"
                     f"🌐 Nós: {m.active_nodes} ativos / {m.total_nodes} total\n"
                     f"⭐ Convergindo: {m.converging_nodes} | Singularidade: {m.singularity_nodes}\n"
                     f"👥 Viewers: {m.total_viewers:,}\n"
                     f"💬 Mensagens: {m.total_messages:,} ({m.messages_per_second:.1f}/s)\n"
                     f"🛡️ Guardian: {m.guardian_efficiency*100:.1f}%\n"
                     f"⚡ Emergências: {m.emergence_events}\n"
                     f"🔐 Selo: {m.canonical_seal or 'N/A'}"
            )]

        elif name == "singularity_emergence":
            history = se.get_emergence_history()
            if not history:
                return [TextContent(type="text", text="📭 Nenhuma emergência registrada")]
            return [TextContent(
                type="text",
                text="\n".join(
                    f"⚡ [{i+1}] ΔΦ_C={e['delta']:+.4f} | {e['phi_c_before']:.4f}→{e['phi_c_after']:.4f} | "
                    f"Nós={e['active_nodes']} | Viewers={e['total_viewers']}"
                    for i, e in enumerate(history[-10:])
                )
            )]

        elif name == "singularity_propagate":
            await se.propagate_seal(arguments["source_node_id"], arguments["target_node_ids"])
            return [TextContent(
                type="text",
                text=f"🔗 Selo propagado de {arguments['source_node_id']} para {len(arguments['target_node_ids'])} nós"
            )]

        elif name == "singularity_prometheus":
            metrics = se.get_prometheus_metrics()
            return [TextContent(type="text", text=f"```prometheus\n{metrics}\n```")]

        raise ValueError(f"Unknown tool: {name}")
