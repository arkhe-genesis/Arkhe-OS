import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from substrate_216.benchmark.uni_kernel_benchmark import UniKernelBenchmark, BenchmarkConfig, ParseMode
from substrate_216.federation.grammar_federation_service import FederatedGrammarClient, GrammarMetadata, GrammarEngine, FederatedGrammar

@pytest.mark.asyncio
async def test_benchmark_run():
    config = BenchmarkConfig(
        languages=["python"],
        sample_sizes=[100],
        iterations_per_sample=1,
        warmup_iterations=0
    )
    benchmark = UniKernelBenchmark(config)
    results = await benchmark.run_benchmark()
    assert len(results) == 2 # kernel and user space
    assert benchmark.comparisons[0].language == "python"

@pytest.mark.asyncio
async def test_federation_client_mock():
    async with FederatedGrammarClient(
        aggregator_url="http://mock",
        org_id="test_org",
        pqc_public_key="mock_key",
        privacy_epsilon=3.0
    ) as client:
        grammars = await client.fetch_global_grammars(["python"])
        assert len(grammars) == 1
        assert grammars[0].language == "python"

        grammar = await client.download_grammar(grammars[0].grammar_id)
        assert grammar is not None
        assert grammar.metadata.language == "python"
