#!/usr/bin/env python3
"""
Arkhe OS - Substrato 213: Tool Calling Production Deployed
"""
import asyncio
import logging
from tools.production_critical_tools import ProductionCriticalToolExecutor, ProductionToolConfig, CriticalToolType
from security.hsm_pqc_production_integration import HSMProductionPQCSigner, HSMProductionConfig
from ml.delta_mem_tool_predictor import DeltaMemToolPredictor
from federation.federated_tool_catalog import FederatedToolCatalog, ToolDiscoveryQuery

logging.basicConfig(level=logging.INFO)

async def main():
    print("ARKHE OS - Substrato 213: Tool Calling Production Deployed")

    # 1. Critical Tools
    config = ProductionToolConfig(
        tool_id="test_api",
        tool_type=CriticalToolType.EXTERNAL_API_CALL,
        endpoint="https://httpbin.org/get",
        credentials_vault_path="mock",
        timeout_seconds=5,
        retry_policy={"max_attempts": 3, "backoff_base": 2, "circuit_cooldown_seconds": 1},
        circuit_breaker_threshold=2,
        rate_limit_per_minute=10,
        requires_pqc_signature=False
    )
    executor = ProductionCriticalToolExecutor(config)
    res = await executor.execute_external_api_call("GET", "https://httpbin.org/get")
    print(f"\n⚒️  Critical Tool Execution: {res['status']}")

    # 2. δ-mem Tool Predictor
    predictor = DeltaMemToolPredictor(delta_mem_wrapper=None, available_tools=["db_query", "api_call"])
    pred = await predictor.predict_optimal_tool("fetch some data")
    print(f"\n🧠 Predição δ-mem: {pred.predicted_tool_id} (confiança: {pred.confidence:.2%})")

    # 3. Federated Catalog
    catalog = FederatedToolCatalog(
        node_id="node_x",
        org_id="org_alpha",
        local_tools={"tool_x": {"capabilities": ["search"], "avg_latency_ms": 50, "success_rate": 0.99}}
    )
    await catalog.publish_local_tools(dp_epsilon=2.0)
    query = ToolDiscoveryQuery(required_capabilities=["search"])
    results = await catalog.discover_tools(query)
    print(f"\n🌐 Descoberta Federada: Encontradas {len(results)} ferramentas compatíveis")

if __name__ == "__main__":
    asyncio.run(main())
