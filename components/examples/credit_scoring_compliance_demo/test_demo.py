import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from arkhe_os.starter.shared.lfir_parser import PolymathLFIRParser, LFIRGraph, LFIRNode, Language
from arkhe_os.starter.shared.compliance_validator import ComplianceValidator, CompliancePredicate, Jurisdiction

def run_demo():
    print("🏦 Running Banking Compliance Demo...")

    # 1. Initialize Validator and Load Predicates
    validator = ComplianceValidator()

    # In a real environment, we'd load from the JSON file:
    # validator.load_predicates_from_file('../../arkhe-starter-java-spring/src/main/resources/predicates/bcb_res_4893.ucspred')

    # For demo, register a dummy predicate directly
    p1 = CompliancePredicate(
        predicate_id="credit_fairness_bcb",
        name="Credit Demographic Parity - BCB",
        description="Fairness checking",
        jurisdictions=[Jurisdiction.BCB],
        ucs_expression="dummy",
        parameters={"optional_for_BCB": False}
    )
    validator.register_predicate(p1)

    # 2. Simulate parsed LFIR
    graph = LFIRGraph(project_id="demo_java", language=Language.JAVA)
    node1 = LFIRNode(
        node_id="n1",
        name="CreditScoringController",
        node_type="class",
        language=Language.JAVA,
        file_path="src/...",
        line_start=10,
        line_end=50,
        regulatory_tags=["BCB"] # This makes it compliant in our mock logic
    )
    graph.add_node(node1)

    # 3. Verify
    print("Verifying artifact...")
    result = validator.verify_artifact("app_123", graph, ["credit_fairness_bcb"], [Jurisdiction.BCB])

    print(f"Is Compliant: {result.is_fully_compliant}")
    print(f"ZK Proof Hash: {result.zk_proof_hash}")

    report = validator.generate_audit_report(result)
    import json
    print("Audit Report:")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_demo()
