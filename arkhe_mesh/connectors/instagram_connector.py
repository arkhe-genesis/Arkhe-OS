#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instagram_connector.py — Conector para Instagram Live
"""

from arkhe_mesh.connectors.base_connector import BroadcastConnector
import logging
import random

logger = logging.getLogger(__name__)

class InstagramConnector(BroadcastConnector):
    def __init__(self):
        super().__init__("Instagram")

    def get_stream_info(self, stream_id: str) -> dict:
        self.metrics["streams_active"] = 1
        viewers = random.randint(50, 5000)
        self.metrics["viewers"] = viewers
        return {
            "platform": self.platform_name,
            "stream_id": stream_id,
            "viewers": viewers,
            "status": "live"
        }

    def process_chat(self, guardian_bus) -> None:
        if not self.is_connected:
            return

        messages = ["Isso é incrível!", "Que live top!", "spam link"]
        for msg in messages:
            self.metrics["messages_processed"] += 1
            # Mock de processamento pelo Guardian
            if "spam" in msg:
                guardian_bus.block_message(self.platform_name, msg)
            else:
                guardian_bus.allow_message(self.platform_name, msg)
