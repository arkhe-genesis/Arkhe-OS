import pytest
import asyncio
from unittest.mock import patch, MagicMock
from substrato_199_windows_fabric import WindowsFabricOrchestrator

@pytest.mark.asyncio
async def test_audit_privacy_security():
    orchestrator = WindowsFabricOrchestrator()
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "Mock Audit Passed"
        mock_run.return_value = mock_result

        result = await orchestrator.audit_privacy_security()

        assert result["status"] == "success"
        assert "Mock Audit Passed" in result["output"]
        mock_run.assert_called_once()
        assert "Test-ArkheDataPrivacy.ps1" in mock_run.call_args[0][0][2]

@pytest.mark.asyncio
async def test_enable_coherence_node():
    orchestrator = WindowsFabricOrchestrator()
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "Node Activated"
        mock_run.return_value = mock_result

        result = await orchestrator.enable_coherence_node()

        assert result["status"] == "success"
        assert "Node Activated" in result["output"]
        mock_run.assert_called_once()
        assert "Enable-ArkheWindowsCoherence.ps1" in mock_run.call_args[0][0][2]

@pytest.mark.asyncio
async def test_run_intelligent_sidecar():
    orchestrator = WindowsFabricOrchestrator()
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "Sidecar Run Success"
        mock_run.return_value = mock_result

        result = await orchestrator.run_intelligent_sidecar()

        assert result["status"] == "success"
        assert "Sidecar Run Success" in result["output"]
        mock_run.assert_called_once()
        assert "arkhe_windows_sidecar.ps1" in mock_run.call_args[0][0][2]
        assert "-RunOnce" in mock_run.call_args[0][0]
