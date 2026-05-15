import pytest
import asyncio
from arkhe_twitch.twitch_connector import TwitchConfig, ArkheTwitchConnector

class MockPhiBus:
    def get_mesh_coherence(self):
        return 0.9999

class MockGuardianReport:
    reason = "unsafe_content"

class MockGuardian:
    def exorcise(self, message):
        if "badword" in message:
            return False, MockGuardianReport()
        return True, None

class MockTemporal:
    async def anchor_event(self, event_type, data):
        return f"seal_for_{event_type}"

class MockPQCResult:
    def __init__(self, success, sig=""):
        self.success = success
        self.signature_or_ciphertext = sig
        self.algorithm_used = "DILITHIUM"
        self.error_message = "error" if not success else ""

class MockPQC:
    def generate_keypair(self):
        return {"private_key": "priv", "public_key": "pub"}
    def sign_message(self, message, key):
        return MockPQCResult(True, "mock_sig_bytes")

@pytest.fixture
def config():
    return TwitchConfig(
        client_id="test_client",
        client_secret="test_secret",
        broadcaster_id="test_broadcaster"
    )

@pytest.mark.asyncio
async def test_stream_info(config):
    connector = ArkheTwitchConnector(
        config=config,
        phi_bus=MockPhiBus(),
        temporal_chain=MockTemporal()
    )
    async with connector as tc:
        stream = await tc.get_stream_info()
        assert stream is not None
        assert stream.title == "ARKHE Cathedral Stream"
        assert stream.phi_c_coherence == 0.9999
        assert stream.temporal_seal == "seal_for_twitch_stream_info"

@pytest.mark.asyncio
async def test_chat_message_process(config):
    connector = ArkheTwitchConnector(
        config=config,
        guardian=MockGuardian(),
        temporal_chain=MockTemporal()
    )
    async with connector as tc:
        safe_msg_data = {
            "message_id": "msg1",
            "broadcaster_user_id": "test_broadcaster",
            "message": {"text": "hello world"}
        }
        msg = await tc.process_chat_message(safe_msg_data)
        assert msg.phi_c_safe is True
        assert len(tc._chat_history) == 1

        unsafe_msg_data = {
            "message_id": "msg2",
            "broadcaster_user_id": "test_broadcaster",
            "message": {"text": "hello badword"}
        }
        msg_unsafe = await tc.process_chat_message(unsafe_msg_data)
        assert msg_unsafe.phi_c_safe is False
        assert msg_unsafe.guardian_reason == "unsafe_content"

@pytest.mark.asyncio
async def test_pqc_signing(config):
    connector = ArkheTwitchConnector(
        config=config,
        phi_bus=MockPhiBus(),
        pqc_adapter=MockPQC()
    )
    async with connector as tc:
        stream = await tc.get_stream_info()
        result = await tc.sign_stream_metadata(stream)
        assert result["success"] is True
        assert "metadata_hash" in result
        assert result["algorithm"] == "DILITHIUM"
