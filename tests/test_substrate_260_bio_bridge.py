import pytest
import asyncio
import sys
import os

# Ensure the module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', '18_bio_integration', '260_bioluminescent_bridge')))
import rluc_enzyme_interface
from rluc_enzyme_interface import RLucPhotovoltaicInterface

@pytest.mark.asyncio
async def test_self_powered_sensor_cycle():
    interface = RLucPhotovoltaicInterface()
    can_transmit, seal = await interface.run_self_powered_sensor_cycle(analyte_detected=True)
    assert isinstance(can_transmit, bool)
    assert isinstance(seal, str)
    assert len(seal) == 64
