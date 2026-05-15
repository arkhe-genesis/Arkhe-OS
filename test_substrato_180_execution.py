import asyncio
from physical.pilot.cluster_setup import PhysicalClusterPilot
from legacy.sandbox.mainframe_emulator import MainframeEmulator, MainframeAccount, TransactionType
from legacy.sandbox.scada_simulator import SCADASimulator, ModbusRegisterType
from specs.formal_verification.verify_continental_mind import SysMLCodeVerifier
from privacy.audit.dp_audit_framework import DifferentialPrivacyAuditor, AuditRequest

class MockOrchestrator:
    async def register_physical_node(self, config): return config
    async def process_sensor_reading(self, *args, **kwargs): pass

async def main():
    print("1. Testing Physical Cluster Pilot")
    pilot = PhysicalClusterPilot(MockOrchestrator())
    await pilot.initialize_cluster(node_count=2)
    print("Physical cluster nodes:", len(pilot.nodes))

    print("2. Testing Mainframe Emulator")
    mf = MainframeEmulator([MainframeAccount("001", "Test", 1000.0)])
    res = await mf.execute_transaction(TransactionType.ACCOUNT_QUERY, {"account_number": "001"}, "user1")
    print("Mainframe response:", res.response_code, res.data)

    print("3. Testing SCADA Simulator")
    scada = SCADASimulator()
    print("SCADA devices:", len(scada.devices))

    print("4. Testing Formal Verification")
    verifier = SysMLCodeVerifier("specs/substrate_178a_continental_mind_spec.sysml", "physical")
    if verifier.parse_sysml_spec():
        print("Spec parsed, constraints:", len(verifier._spec_constraints))

    print("5. Testing DP Audit Framework")
    auditor = DifferentialPrivacyAuditor()
    req = AuditRequest("auditor_1", 1, "hash1", 1.0, 1e-5, "commitment")
    audit_id = await auditor.request_audit(req)
    print("Audit requested with ID:", audit_id)

if __name__ == "__main__":
    asyncio.run(main())
