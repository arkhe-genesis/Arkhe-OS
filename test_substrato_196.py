import pytest
import os
import sys

# Adicionar a pasta do boilerplate ao PYTHONPATH para os testes
sys.path.insert(0, os.path.abspath("arkhe-service-template"))

def test_boilerplate_structure():
    assert os.path.exists("arkhe-service-template/src/service.py")
    assert os.path.exists("arkhe-service-template/src/sidecar.py")
    assert os.path.exists("arkhe-service-template/src/security.py")
    assert os.path.exists("arkhe-service-template/tests/test_service.py")
    assert os.path.exists("arkhe-service-template/Dockerfile")
    assert os.path.exists("arkhe-service-template/k8s/deployment.yaml")
