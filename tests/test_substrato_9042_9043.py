import asyncio
from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh, TwitchConfig
from substrato_9042_arkhe_twitch import ArkheTwitchSingularity
from substrato_9043_cross_platform_mesh import MultiPlatformMesh
from arkhe_twitch.youtube_live_connector import YouTubeConfig
from arkhe_twitch.tiktok_live_connector import TikTokConfig

def test_twitch_singularity():
    async def run():
        se = ArkheTwitchSingularity()
        node = se.register_node("broadcaster_1", "Stream 1", "stream_1", 0.9999)
        assert node.status.value == "active"
        await se.update_node_metrics(node.node_id, 100, 10, 0.9999)
        assert se._metrics.singularity_nodes == 1
        assert se._metrics.global_phi_c == 0.9999
    asyncio.run(run())

def test_mesh_orchestrator():
    async def run():
        mesh = CoherentBroadcastMesh()
        config = TwitchConfig("client_id", "client_secret", "b_id")
        stream = await mesh.add_stream("s1", config)
        assert stream.active is False
    asyncio.run(run())

def test_multi_platform_mesh():
    async def run():
        mesh = MultiPlatformMesh()
        tw_cfg = TwitchConfig("c", "s", "b")
        await mesh.add_twitch("tw1", tw_cfg)

        yt_cfg = YouTubeConfig("c", "s", "r", "ch", "api")
        await mesh.add_youtube("yt1", yt_cfg)

        tk_cfg = TikTokConfig("ck", "cs", "a", "o")
        await mesh.add_tiktok("tk1", tk_cfg)

        st = await mesh.get_mesh_status()
        assert len(st["streams"]) == 1 # Only tw mocked correctly to return true get_stream_info in this simple test
    asyncio.run(run())
