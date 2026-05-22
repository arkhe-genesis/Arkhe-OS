import pytest
import os
import sys

def test_validation():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from validation.collective_sandbox import validate_collective_emergence
    import asyncio
    assert asyncio.run(validate_collective_emergence()) == True

def test_fips():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from fips.collective_fips import certify_collective_modules
    assert certify_collective_modules() == True

def test_expansion():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from expansion.multi_neuron_expansion import expand_neural_diversity
    import asyncio
    assert asyncio.run(expand_neural_diversity()) == True

import json

def test_substrato_564():
    sys.path.append(os.path.abspath('substrates/500-599_advanced/substrato_564_mcp_stateless_bridge'))
    from substrato_564_mcp_stateless_bridge import Substrate564McpStatelessBridge
    substrate = Substrate564McpStatelessBridge()
    path = substrate.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data['substrate'] == '564-MCP-STATELESS-BRIDGE'
    assert data['phi_c'] == 0.991944
    assert data['canonical_seal'] == '264a97ee1fcd994e58f42d1f14635e07c1ef97fef615eacf27dbbe069943cc79'
    assert 'quantum_simulate_circuit' in data['tools']

if __name__ == '__main__':
    pytest.main(['-v', 'test_substrates.py'])
