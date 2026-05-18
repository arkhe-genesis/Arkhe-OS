import pytest
import time
from substrates.substrato_221_energy_oracle import EnergyOracle

@pytest.mark.asyncio
async def test_energy_oracle():
    oracle = EnergyOracle()

    # Initial state should be base price because _last_update is 0
    # So the first call to get_current_price will update the price
    price1 = await oracle.get_current_price()
    assert 30 <= price1 <= 200

    # Calling again immediately should return cached price
    price2 = await oracle.get_current_price()
    assert price1 == price2

    # Mocking time to simulate 61 seconds passing
    import time
    original_time = time.time

    # We will patch time.time locally
    class TimeMock:
        def __init__(self, current):
            self.current = current
        def __call__(self):
            return self.current

    import mock
    with mock.patch('time.time', side_effect=[time.time() + 65, time.time() + 65]):
        # This will trigger an update
        price3 = await oracle.get_current_price()
        # Very small chance it generates exactly the same float
        # but realistically it should update

    # Test adjust_gas
    base_gas = 100.0
    adjusted_gas = await oracle.adjust_gas(base_gas)
    # the last cached price was used
    expected_gas = base_gas * (oracle._cached_price / oracle.base_price_mwh)
    assert adjusted_gas == expected_gas
