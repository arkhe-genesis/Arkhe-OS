import pytest
import json
from substrato_377_bis import Substrato377Bis

def test_canonization():
    sub = Substrato377Bis()
    result = sub.process()
    assert result["substrato"] == "377-BIS"
    assert result["cenario"] == "AGI_TRAINED_HISTORICAL_CALIBRATION"
    assert result["veredicto"] == "CANONIZED"
    assert "US-NV" in result["training_data"]
    assert "BR-SP" in result["training_data"]
    assert "DE-HE" in result["training_data"]
    assert "JP-13" in result["training_data"]
