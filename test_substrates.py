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

if __name__ == '__main__':
    pytest.main(['-v', 'test_substrates.py'])
