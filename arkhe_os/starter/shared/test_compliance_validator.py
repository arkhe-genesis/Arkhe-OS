import unittest
from arkhe_os.starter.shared.lfir_parser import LFIRGraph, LFIRNode, Language
from arkhe_os.starter.shared.compliance_validator import ComplianceValidator, CompliancePredicate, Jurisdiction

class TestComplianceValidator(unittest.TestCase):
    def test_compliance(self):
        validator = ComplianceValidator()
        p1 = CompliancePredicate(
            predicate_id="test_pred",
            name="Test",
            description="Test desc",
            jurisdictions=[Jurisdiction.BCB],
            ucs_expression="dummy"
        )
        validator.register_predicate(p1)

        graph = LFIRGraph(project_id="test_proj", language=Language.JAVA)
        node = LFIRNode(
            node_id="n1",
            name="TestNode",
            node_type="class",
            language=Language.JAVA,
            file_path="src/...",
            line_start=1,
            line_end=10,
            regulatory_tags=["BCB"]
        )
        graph.add_node(node)

        result = validator.verify_artifact("app_test", graph, ["test_pred"], [Jurisdiction.BCB])
        self.assertTrue(result.is_fully_compliant)

if __name__ == '__main__':
    unittest.main()
