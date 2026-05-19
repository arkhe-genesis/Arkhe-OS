import pytest
import hashlib
from src.cathedral.legal.stf_asi_tpi_bridge import STF_ASITPIBridge

@pytest.fixture
def stf_bridge():
    return STF_ASITPIBridge()

def test_submit_national_case(stf_bridge):
    evidence = [
        hashlib.sha3_256(b"prova_1").hexdigest(),
        hashlib.sha3_256(b"prova_2").hexdigest(),
        hashlib.sha3_256(b"prova_3").hexdigest()
    ]

    submission = stf_bridge.submit_national_case(
        "STF-ADO-59",
        "Proteção da Soberania Algorítmica Nacional",
        ["Violação de Soberania de Agência", "Dano Epistêmico"],
        evidence
    )

    assert submission["status"] == "submitted"
    assert submission["stf_case"] == "STF-ADO-59"
    assert "ASI-TPI" in submission["asi_tpi_case"]

def test_execute_national_verdict(stf_bridge):
    evidence = [
        hashlib.sha3_256(b"prova_1").hexdigest(),
        hashlib.sha3_256(b"prova_2").hexdigest(),
        hashlib.sha3_256(b"prova_3").hexdigest()
    ]

    stf_bridge.submit_national_case(
        "STF-ADO-60",
        "Fraude e Manipulação na Eleição",
        ["Fraude Algorítmica"],
        evidence
    )

    execution = stf_bridge.execute_national_verdict("STF-ADO-60")

    assert "verdict" in execution
    assert execution["verdict"] in ["guilty", "innocent"]
    if execution["verdict"] == "guilty":
        assert "enforcement" in execution
        assert "stf_return_seal" in execution

def test_execute_nonexistent_case(stf_bridge):
    execution = stf_bridge.execute_national_verdict("STF-INEXISTENTE-99")
    assert "error" in execution
