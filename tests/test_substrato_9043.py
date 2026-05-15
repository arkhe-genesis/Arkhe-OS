import pytest
from arkhe_mesh.connectors.instagram_connector import InstagramConnector
from arkhe_mesh.connectors.kick_connector import KickConnector
from arkhe_mesh.connectors.trovo_connector import TrovoConnector
from security.vault_hsm_manager import VaultHSMManager
from arkhe_spark.mesh_tuning import SparkMeshTuning
from monitoring.mesh_prometheus_exporter import MeshPrometheusExporter

class MockGuardianBus:
    def __init__(self):
        self.blocks = 0
    def block_message(self, platform, msg):
        self.blocks += 1
    def allow_message(self, platform, msg):
        pass

def test_vault_hsm_manager():
    manager = VaultHSMManager()
    token = manager.get_oauth_token("twitch")
    assert token is not None
    assert "init_twitch" in token

    # Test PQC signing
    sig = manager.sign_metadata_pqc("test_data")
    assert len(sig) == 128  # sha3_512 hex length

def test_connectors():
    vault = VaultHSMManager()
    guardian = MockGuardianBus()

    connectors = [InstagramConnector(), KickConnector(), TrovoConnector()]
    for conn in connectors:
        assert conn.connect(vault) == True
        info = conn.get_stream_info("123")
        assert info["platform"] == conn.platform_name
        assert info["viewers"] > 0

        conn.process_chat(guardian)
        metrics = conn.get_metrics()
        assert metrics["messages_processed"] > 0

def test_spark_tuning():
    tuning = SparkMeshTuning()
    config = tuning.get_spark_config()
    assert config["spark.streaming.batchInterval"] == "5s"
    assert config["spark.sql.adaptive.enabled"] == True

def test_prometheus_exporter():
    exporter = MeshPrometheusExporter()
    exporter.start_server(8000)
    assert exporter.active == True

    exporter.update_metrics(10, 5000, 0.99, 1000, 5, 2.5, 50)
    assert exporter.metrics["arkhe_mesh_streams_active"].value == 10
    assert exporter.metrics["arkhe_mesh_viewers_total"].value == 5000
    assert exporter.metrics["arkhe_chat_messages_total"].value == 1000
