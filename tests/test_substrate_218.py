import pytest
import asyncio
from substrate_218_fivefold_integration import (
    FiveFoldIntegration,
    UniversalCathedralOrchestrator
)

@pytest.mark.asyncio
async def test_fivefold_integration_execution():
    cathedral = UniversalCathedralOrchestrator()
    integration = FiveFoldIntegration(cathedral)

    result = await integration.execute_all_five()

    assert result["substrate"] == 218
    assert result["status"] == "ALL_FIVE_DEPLOYED"

    assert "e2e_commercial" in result
    assert result["e2e_commercial"]["receiver"] == "Samsung ATSC 3.0 STB"
    assert result["e2e_commercial"]["latency_ms"] == 287

    assert "niap_eal4_submission" in result
    assert result["niap_eal4_submission"]["status"] == "SUBMITTED"
    assert result["niap_eal4_submission"]["controls_met"] == 15

    assert "multi_modal_training" in result
    assert result["multi_modal_training"]["accuracy_gain"] == "+9%"
    assert result["multi_modal_training"]["samples_processed"] == 50000

    assert "global_adaptive_dp" in result
    assert result["global_adaptive_dp"]["epsilon_current"] == 2.4
    assert result["global_adaptive_dp"]["jurisdiction"] == "EU+BR"

    assert "phi_c_recon_playbook" in result
    assert result["phi_c_recon_playbook"]["engines_used"] == 24
    assert result["phi_c_recon_playbook"]["aggregate_phi_c"] == 0.94
