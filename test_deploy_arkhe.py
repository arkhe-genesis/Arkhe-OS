import subprocess

def test_deploy_arkhe_sh_execution():
    result = subprocess.run(["./deploy_arkhe.sh"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "ARKHE Ω-TEMP v∞.Ω — SUBSTRATO 9046: DEPLOYMENT ORCHESTRATOR" in result.stdout
    assert "Validating prerequisites..." in result.stdout
    assert "Deploying Kubernetes manifest sequence..." in result.stdout
    assert "Kubernetes stack deployed successfully." in result.stdout
    assert "Executing post-deploy smoke tests..." in result.stdout
    assert "Anchoring deployment to TemporalChain..." in result.stdout
    assert "TemporalChain Anchor Complete." in result.stdout
    assert "Deployment Orchestrator 9046 Execution Finished Successfully." in result.stdout

def test_deploy_arkhe_ps1_content():
    with open("deploy_arkhe.ps1", "r") as f:
        content = f.read()
    assert "ARKHE Ω-TEMP v∞.Ω — SUBSTRATO 9046: DEPLOYMENT ORCHESTRATOR" in content
    assert "Validating prerequisites..." in content
    assert "Deploying Kubernetes manifest sequence..." in content
    assert "Executing post-deploy smoke tests..." in content
    assert "Anchoring deployment to TemporalChain..." in content
    assert "Deployment Orchestrator 9046 Execution Finished Successfully." in content
