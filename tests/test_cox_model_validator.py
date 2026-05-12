import pytest
from conrag.domains.sociology_rules import CoxModelValidator

def test_cox_model_validator_valid():
    validator = CoxModelValidator()
    result = validator.validate_model(
        p_value=0.06,  # > 0.05
        max_vif=4.0,   # < 5.0
        is_linear=True,
        is_independent=True
    )
    assert result["is_valid"] is True
    assert result["details"]["proportional_hazards"][0] is True
    assert result["details"]["multicollinearity"][0] is True
    assert result["details"]["linearity"][0] is True
    assert result["details"]["independence"][0] is True

def test_cox_model_validator_invalid_p_value():
    validator = CoxModelValidator()
    result = validator.validate_model(
        p_value=0.04,  # <= 0.05
        max_vif=4.0,
        is_linear=True,
        is_independent=True
    )
    assert result["is_valid"] is False
    assert result["details"]["proportional_hazards"][0] is False

def test_cox_model_validator_invalid_vif():
    validator = CoxModelValidator()
    result = validator.validate_model(
        p_value=0.06,
        max_vif=6.0,  # >= 5.0
        is_linear=True,
        is_independent=True
    )
    assert result["is_valid"] is False
    assert result["details"]["multicollinearity"][0] is False
