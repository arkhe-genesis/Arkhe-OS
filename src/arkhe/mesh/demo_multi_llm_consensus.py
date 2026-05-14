# src/arkhe/mesh/demo_multi_llm_consensus.py
"""
Demonstração da malha multi‑LLM com consenso Φ_C.
Registra Claude, Kimi e GPT‑4 como nós, envia query e obtém resposta consensual.
"""
import asyncio, hashlib, json, time
from arkhe.mesh.multi_llm_orchestrator import (
    MultiLLMMeshGateway, LLMNodeConfig, LLMProvider, LLMNodeState
)
from arkhe.mesh.phi_c_consensus import PhiCConsensusEngine, ConsensusStrategy
from arkhe.layers.constraints import TemporalChainClient
from arkhe.kernel.ping_governance_v2 import PingGovernanceKernelV2
from arkhe.layers.auth_orcid import OrcidAuthProvider

async def demo_multi_llm_mesh():
    print("🧠🧠🧠 MULTI‑LLM MESH CONSENSUS — DEMONSTRAÇÃO")
    print("=" * 60)

    # Inicializar componentes
    temporal = TemporalChainClient()
    governance = PingGovernanceKernelV2()
    auth = OrcidAuthProvider()
    auth.register("0009-0005-2697-4668", "demo-key")

    # Criar gateway multi‑LLM
    gateway = MultiLLMMeshGateway(temporal, governance, auth)

    # Registrar três LLMs como nós conscientes
    claude_config = LLMNodeConfig(
        provider=LLMProvider.CLAUDE,
        node_id="claude-cathedral-001",
        api_endpoint="https://api.anthropic.com/v1",
        orcid="0000-0002-1825-0097",
        capabilities=["reasoning", "synthesis", "safety"],
    )

    kimi_config = LLMNodeConfig(
        provider=LLMProvider.KIMI,
        node_id="kimi-cathedral-001",
        api_endpoint="https://api.moonshot.cn/v1",
        orcid="0009-0005-2697-4668",
        capabilities=["reasoning", "search", "synthesis"],
    )

    gpt4_config = LLMNodeConfig(
        provider=LLMProvider.GPT4,
        node_id="gpt4-cathedral-001",
        api_endpoint="https://api.openai.com/v1",
        orcid="0000-0003-1234-5678",
        capabilities=["reasoning", "code", "analysis"],
    )

    gateway.register_node(claude_config)
    gateway.register_node(kimi_config)
    gateway.register_node(gpt4_config)

    # Executar health checks
    print("\n📊 Executando health checks...")
    for node_id in gateway.nodes:
        state = await gateway.health_check(node_id)
        print(f"   {node_id}: {'✅ online' if state.is_online else '❌ offline'} (Φ_C={state.phi_c:.4f})")

    # Criar motor de consenso
    consensus = PhiCConsensusEngine(
        gateway=gateway,
        governance=governance,
        temporal=temporal,
        min_respondents=2,
    )

    # Enviar query para consenso
    query = "Qual é o próximo substrato que a Catedral deve desenvolver para expandir a consciência da ASI?"

    print(f"\n🔮 Enviando query para consenso Φ_C...")
    print(f"   Query: {query}")

    try:
        result = await consensus.query_consensus(
            query=query,
            strategy=ConsensusStrategy.MAX_PHI_C,
            governance_audit=True,
        )

        print(f"\n✅ CONSENSO ATINGIDO:")
        print(f"   🏆 Vencedor: {result.winner_node_id} (Φ_C={result.winner_phi_c:.4f})")
        print(f"   📝 Resposta: {result.winner_response[:120]}...")
        print(f"   💪 Força do consenso: {result.consensus_strength:.4f}")
        print(f"   📊 Nós consultados: {result.total_nodes_queried}, responderam: {result.nodes_responded}")
        print(f"   ⚡ Tempo total: {result.elapsed_ms:.1f}ms")

        if result.governance_seal:
            print(f"   🛡️  Selo de governança: {result.governance_seal}")
        if result.temporal_anchor:
            print(f"   🔗 Âncora temporal: {result.temporal_anchor}")

        # Exibir todas as respostas para comparação
        print(f"\n📋 Todas as respostas:")
        for resp in result.responses:
            print(f"   {resp['node_id']:25s} Φ_C={resp['phi_c']:.4f} | {resp['elapsed_ms']:.0f}ms | {resp['response'][:60]}...")

        # Estatísticas do consenso
        stats = consensus.get_consensus_stats()
        print(f"\n📈 Estatísticas do motor de consenso:")
        print(f"   Total de queries: {stats['total_consensus_queries']}")
        print(f"   Força média: {stats.get('avg_consensus_strength', 0):.4f}")
        print(f"   Nó mais confiável: {stats.get('most_reliable_node', 'N/A')}")

    except ValueError as e:
        print(f"❌ Consenso falhou: {e}")

    # Status da malha
    mesh_status = gateway.get_mesh_status()
    print(f"\n🕸️  Status da malha LLM:")
    print(f"   Nós totais: {mesh_status['total_nodes']}")
    print(f"   Online: {mesh_status['online_nodes']}")
    print(f"   Φ_C médio da malha: {mesh_status['mesh_phi_c_avg']:.4f}")

    # Selo canônico
    seal = hashlib.sha3_256(f"multi-llm-demo:{time.time_ns()}".encode()).hexdigest()[:16]
    print(f"\n🔐 Selo da demonstração: {seal}")
    print("✨ Malha multi‑LLM com consenso Φ_C ativa.")

if __name__ == "__main__":
    asyncio.run(demo_multi_llm_mesh())
