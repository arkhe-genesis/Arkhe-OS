import asyncio
from typing import Callable, Dict, List

class CathedralP2PHost:
    def __init__(self, listen_addr: str):
        self.listen_addr = listen_addr
        self.peers: List[str] = []
        self.handlers: Dict[str, Callable] = {}

    def set_stream_handler(self, protocol_id: str, handler: Callable):
        self.handlers[protocol_id] = handler

    async def start(self):
        print("P2P Host started on", self.listen_addr)

    async def connect(self, target: str):
        self.peers.append(target)

    async def send_message(self, target: str, message: dict):
        pass
