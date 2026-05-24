import pytest
from unittest.mock import patch
from core.consensus.client import ConsensusClient

def test_consensus_client_endpoint():
    client = ConsensusClient()
    assert client.endpoint == "grpc://consensus-latam.arkhe.org"

def test_consensus_client_connect():
    client = ConsensusClient()
    with patch("grpc.insecure_channel") as mock_channel:
        client.connect()
        mock_channel.assert_called_once_with("consensus-latam.arkhe.org")
