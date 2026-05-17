import pytest
import os
import tempfile
import asyncio

from substrates.substrato_237_dsvpn_canonization import DSVPNCanonicalTool, DSVPNConfig

@pytest.mark.asyncio
async def test_dsvpn_canonization():
    with tempfile.TemporaryDirectory() as temp_dir:
        key_path = os.path.join(temp_dir, "vpn.key")

        tool = DSVPNCanonicalTool()

        # Generate Key
        key = await tool.generate_key(key_path=key_path, use_hsm=False)
        assert os.path.exists(key_path)
        assert key.derivation_source == "urandom"
        assert key.key_path == key_path

        # Start Server
        server_config = DSVPNConfig(mode="server", key_file=key_path, server_ip="0.0.0.0", port=443)
        server_tunnel = await tool.start_server(server_config)
        assert server_tunnel.mode == "server"
        assert server_tunnel.status == "active"
        assert server_tunnel.tunnel_id in tool._active_tunnels

        # Start Client
        client_config = DSVPNConfig(mode="client", key_file=key_path, server_ip="127.0.0.1", port=443)
        client_tunnel = await tool.start_client(client_config)
        assert client_tunnel.mode == "client"
        assert client_tunnel.status == "active"
        assert client_tunnel.tunnel_id in tool._active_tunnels

        # Test Heartbeats
        await asyncio.sleep(0.01)
        hb_server = await tool.heartbeat(server_tunnel.tunnel_id)
        assert hb_server is True
        assert server_tunnel.bytes_sent > 0
        assert server_tunnel.bytes_received > 0

        hb_client = await tool.heartbeat(client_tunnel.tunnel_id)
        assert hb_client is True
        assert client_tunnel.bytes_sent > 0
        assert client_tunnel.bytes_received > 0

        # Invalid Heartbeat
        hb_invalid = await tool.heartbeat("invalid_id")
        assert hb_invalid is False

        # Test Statistics
        stats = tool.get_statistics()
        assert stats["total_tunnels"] == 2
        assert stats["active_servers"] == 1
        assert stats["active_clients"] == 1
        assert stats["total_keys_generated"] == 1
        assert stats["total_operations"] == 3 # 1 key + 1 server + 1 client
        assert stats["total_bytes_transferred"] > 0

        # Test Manifesto
        manifest = tool.export_canonical_manifest()
        assert manifest["substrate_id"] == "237"
        assert "simplicity_radical" in manifest["principles"]

        # Stop Tunnels
        stop_server = await tool.stop_tunnel(server_tunnel.tunnel_id)
        assert stop_server is True
        assert server_tunnel.tunnel_id not in tool._active_tunnels

        stop_client = await tool.stop_tunnel(client_tunnel.tunnel_id)
        assert stop_client is True
        assert client_tunnel.tunnel_id not in tool._active_tunnels

        # Invalid Stop
        stop_invalid = await tool.stop_tunnel("invalid_id")
        assert stop_invalid is False
