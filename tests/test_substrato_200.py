import pytest
import asyncio
from banking.core_settlement import CoreSettlement
from banking.fraud_detection import FraudDetector
from banking.compliance_automation import ComplianceAutomation
from banking.custody import QuantumCustody
from banking.rtgs import RTGS
from banking.trade_finance import TradeFinance

@pytest.mark.asyncio
async def test_core_settlement():
    settlement = CoreSettlement()
    # Should reject due to low Phi_C
    res_low_phi = await settlement.process_settlement("BankA", "BankB", 1000, ["A", "B", "C"], current_phi_c=0.98)
    assert res_low_phi.status == "REJECTED"

    # Should succeed
    res_success = await settlement.process_settlement("BankA", "BankB", 1000, ["A", "B", "C"], current_phi_c=0.9995)
    assert res_success.status == "SETTLED"
    assert res_success.temporal_seal is not None
    assert res_success.pqc_signature is not None

@pytest.mark.asyncio
async def test_fraud_detection():
    detector = FraudDetector()
    detector.train_model([{"amount": 10}, {"amount": 20}, {"amount": 15}])

    # Highly anomalous transaction
    alert = await detector.evaluate_transaction({"amount": 1000000, "velocity_1h": 50, "distance_km": 10000}, current_phi_c=0.99)
    assert alert.anomaly_score > 0.5
    assert alert.risk_level in ["high", "critical"]

@pytest.mark.asyncio
async def test_compliance_automation():
    compliance = ComplianceAutomation()

    # Invalid framework
    with pytest.raises(ValueError):
        await compliance.generate_report("INVALID", {})

    # Valid framework
    report = await compliance.generate_report("BACEN", {"total_exposure": 1000})
    assert report.framework == "BACEN"
    assert report.pqc_signature is not None

@pytest.mark.asyncio
async def test_quantum_custody():
    custody = QuantumCustody()
    asset = await custody.deposit("BTC", 10.5, "owner123")
    assert asset.symbol == "BTC"

    # Invalid withdraw (wrong owner)
    with pytest.raises(ValueError):
        await custody.withdraw(asset.asset_id, "wrong_owner", asset.epr_witness)

    # Valid withdraw
    withdrawn = await custody.withdraw(asset.asset_id, "owner123", asset.epr_witness)
    assert withdrawn.amount == 10.5

@pytest.mark.asyncio
async def test_rtgs():
    rtgs = RTGS()

    # low phi_c
    tx1 = await rtgs.execute_transfer("BankA", "BankB", 500, current_phi_c=0.95)
    assert tx1.status == "REJECTED_LOW_PHI_C"

    # high phi_c
    tx2 = await rtgs.execute_transfer("BankA", "BankB", 500, current_phi_c=0.999)
    assert tx2.status == "SETTLED"
    assert tx2.quantum_proof.startswith("qproof_")

@pytest.mark.asyncio
async def test_trade_finance():
    tf = TradeFinance(dp_epsilon=1.0)
    contract = await tf.create_contract("Imp", "Exp", 10000.0)
    assert contract.status == "DRAFT"

    tf.update_contract_status(contract.contract_id, "CONFIRMED")
    assert tf.contracts[contract.contract_id].status == "CONFIRMED"

    exposure = tf.get_portfolio_exposure()
    assert exposure["total_active_contracts"] == 1
    # Noise is added, so just check it's a float
    assert isinstance(exposure["dp_noisy_exposure"], float)
