from core.substrate_runtime import SubstrateRuntime
from core.ledger_sync import LedgerSync
from sdks.federated_client import FederatedClient

def test_client_server_ledger():
    client = FederatedClient()
    proof = client.generate_proof("test_data")

    runtime = SubstrateRuntime()
    # Dummy verification logic
    verified = True

    ledger = LedgerSync()
    if verified:
        ledger.sync_octra(proof)

    assert len(ledger.ledger) == 1
    assert ledger.ledger[0] == "proof_test_data"
