class APIGateway:
    def __init__(self):
        self.routes = {}

    def add_route(self, path, handler):
        self.routes[path] = handler

    def auth_middleware(self, request):
        if "Authorization" in request:
            return True
        return False

def run_gateway():
    gateway = APIGateway()
    return gateway
