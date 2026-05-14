import unittest
from arkhe.layers.engineering.schema_migration import SchemaVersion

class TestSchemaMigration(unittest.TestCase):
    def test_schema_version_checksum(self):
        sv = SchemaVersion(1, "CREATE TABLE t (id INT)", "DROP TABLE t")
        sv.compute_checksum()
        self.assertTrue(len(sv.checksum) > 0)
