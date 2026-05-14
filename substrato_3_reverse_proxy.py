import random

class Substrato3ReverseProxy:
    def __init__(self, backends):
        """Initializes with a list of backend nodes."""
        self.backends = backends

    def handle_request(self, request_data: str) -> str:
        """Routes a request to a random backend and returns the response."""
        if not self.backends:
            return "502 Bad Gateway: No backends available"

        # Simple random load balancing
        selected_backend = random.choice(self.backends)
        return self._forward_request(selected_backend, request_data)

    def _forward_request(self, backend: str, request_data: str) -> str:
        """Simulates forwarding the request to the backend."""
        # In a real implementation, this would make a network call to the backend.
        return f"Response from {backend} for request: {request_data}"

if __name__ == "__main__":
    proxy = Substrato3ReverseProxy(["backend1:8080", "backend2:8080", "backend3:8080"])
    print(proxy.handle_request("GET /api/data"))
    print(proxy.handle_request("POST /api/data"))
