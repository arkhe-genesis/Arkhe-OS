import json
import asyncio
import threading
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .passport_gateway import PassportGateway

class APIGateway:
    def __init__(self, node_id: str, passport: Optional[PassportGateway] = None):
        self.node_id = node_id
        self.queries_processed = 0
        self.passport = passport

    def handle_ws_message(self, message: str) -> str:
        # Mocking existing method
        return "{}"

    async def start_http_server(self):
        server = HTTPServer(("0.0.0.0", 8080), lambda *args: self.RequestHandler(*args, gateway=self))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"Server listening on port 8080")

    class RequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, gateway=None, **kwargs):
            self.gateway = gateway
            super().__init__(*args, **kwargs)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/v1/status":
                self.send_json(200, {"status": "ok"})
            elif path == "/v1/oracle/feeds":
                self.send_json(200, {"feeds": []})
            elif path.startswith("/v1/identity/passport"):
                # Ex: /v1/identity/passport?address=0x...
                params = parse_qs(urlparse(self.path).query)
                address = params.get("address", [None])[0]
                if not address:
                    self.send_error(400, "Missing address")
                    return
                # We need a new event loop inside this thread to run async logic
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Quick hack to get results synchronously from passport methods
                async def _run_checks():
                    # temporarily instantiate a separate gateway to ensure loop isolation
                    # or ensure we do NOT use same aiohttp session concurrently
                    gw = PassportGateway()
                    await gw.start()
                    try:
                        res = await gw.is_human(address)
                        return res
                    finally:
                        await gw.stop()
                try:
                    proof = loop.run_until_complete(_run_checks())
                    self.send_json(200, {
                        "address": proof.address,
                        "is_human": proof.is_human,
                        "score": proof.score,
                        "stamps": proof.stamps,
                        "orcid_verified": proof.orcid_verified,
                    })
                except Exception as e:
                    self.send_error(500, str(e))
                finally:
                    loop.close()
            elif path.startswith("/v1/dao/verify-voter"):
                params = parse_qs(urlparse(self.path).query)
                address = params.get("address", [None])[0]
                if not address:
                    self.send_error(400, "Missing address")
                    return
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                async def _run_checks():
                    gw = PassportGateway()
                    await gw.start()
                    try:
                        return await gw.verify_dao_voter(address)
                    finally:
                        await gw.stop()
                try:
                    can_vote = loop.run_until_complete(_run_checks())
                    self.send_json(200, {"address": address, "can_vote": can_vote})
                except Exception as e:
                    self.send_error(500, str(e))
                finally:
                    loop.close()
            else:
                self.send_error(404, "Not found")

        def send_json(self, status: int, data: dict):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
