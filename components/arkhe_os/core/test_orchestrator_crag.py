import asyncio
from unittest.mock import MagicMock
from arkhe_os.core.unified_orchestrator import UnifiedFieldOrchestrator

async def run_test():
    print("Testing C-RAG Integration with Orchestrator v149...")
    mock_field = MagicMock()
    mock_ethics = MagicMock()

    orchestrator = UnifiedFieldOrchestrator(mock_field, mock_ethics)

    query = "Explain geodesic cache in Substrate 154"
    result = await orchestrator.process_c_rag_query(query, "Context about geodesic caching", zone="alpha")

    print("\n[RESULT]")
    print(f"Generated: {result['generated_text']}")
    print(f"Hallucination Flag: {result['safety']['hallucination_flag']}")
    print(f"Merkle Proof: {result['merkle_proof']}")
    print(f"Latency: {result['latency_ms']:.2f} ms")

    # Test caching
    print("\nTesting Distributed Geodesic Cache...")
    result2 = await orchestrator.process_c_rag_query(query, "Context about geodesic caching", zone="alpha")
    if result2 is result:
        print("Cache HIT - Successfully loaded from Distributed Geodesic Cache")
    else:
        print("Cache MISS - Failed to load from Distributed Geodesic Cache")

if __name__ == "__main__":
    asyncio.run(run_test())
