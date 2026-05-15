import sys
import unittest
import asyncio

from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh
from arkhe_broadcast.youtube_live_connector import YouTubeLiveConnector, YouTubeConfig
from arkhe_broadcast.tiktok_live_connector import TikTokLiveConnector, TikTokConfig
from arkhe_broadcast.twitch_connector import ArkheTwitchConnector, TwitchConfig
from arkhe_spark.spark_distributed_processor import DistributedChatProcessor
from arkhe_mcp.server import ArkheMCPServer

class TestFullBroadcast(unittest.TestCase):
    def test_imports_and_instantiation(self):
        m = CoherentBroadcastMesh()
        yc = YouTubeConfig()
        tc = TikTokConfig()
        twc = TwitchConfig()
        sp = DistributedChatProcessor()
        mcp = ArkheMCPServer()
        self.assertIsNotNone(m)

if __name__ == '__main__':
    unittest.main()
