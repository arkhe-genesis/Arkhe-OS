import pytest
import asyncio
from unittest.mock import MagicMock, patch

from security.maintainer_pqc_verifier import MaintainerPQCVerifier
from security.vulnerability_auditor import VulnerabilityAuditor
from pypi.pypi_canonical_tool import PyPICanonicalTool
from pypi.polyglot_orchestrator import PolyglotOrchestrator

@pytest.mark.asyncio
async def test_maintainer_pqc_verifier():
    verifier = MaintainerPQCVerifier()
    assert await verifier.verify_package_signature("requests", "2.31.0") is True

@pytest.mark.asyncio
async def test_vulnerability_auditor():
    auditor = VulnerabilityAuditor()
    res = await auditor.audit_package("requests", "2.31.0")
    assert res["vulnerabilities"] == 0

@pytest.mark.asyncio
async def test_pypi_canonical_tool_with_security():
    pqc = MaintainerPQCVerifier()
    vuln = VulnerabilityAuditor()
    tool = PyPICanonicalTool(working_dir="/tmp", pqc_verifier=pqc, vuln_auditor=vuln)

    with patch.object(tool, '_run_command', return_value={"returncode": 0}) as mock_run:
        res = await tool.pip_install({"package": "requests", "version": "2.31.0"})
        assert res.get("returncode") == 0
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_polyglot_orchestrator():
    pypi_mock = MagicMock()
    pypi_future = asyncio.Future()
    pypi_future.set_result({"status": "success", "returncode": 0})
    pypi_mock.pip_install.return_value = pypi_future

    npm_mock = MagicMock()
    npm_future = asyncio.Future()
    npm_future.set_result({"status": "success", "returncode": 0})
    npm_mock.install_dependencies.return_value = npm_future

    orch = PolyglotOrchestrator(pypi_mock, npm_mock)
    res = await orch.install_polyglot_project("/tmp/app", {"package": "requests"})

    assert res["status"] == "success"
    assert res["pypi"]["status"] == "success"
    assert res["npm"]["status"] == "success"
