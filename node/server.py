from .passport_gateway import PassportGateway
from .api_gateway import APIGateway

class ArkheNode:
    def __init__(self, config_path: str = "config.yaml"):
        self.node_id = "node-001"
        self.config = {"passport_enabled": True}
        self.passport = PassportGateway()
        self.api = APIGateway(node_id=self.node_id, passport=self.passport)

    async def start(self):
        if self.config.get("passport_enabled", True):
            await self.passport.start()
        await self.api.start_http_server()
