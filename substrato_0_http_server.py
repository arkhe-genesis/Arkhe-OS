import socket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("substrato_0")

class Substrato0HTTPServer:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            logger.info(f"Substrato 0 HTTP Server running on {self.host}:{self.port}")

            # Simple run loop that doesn't block indefinitely in tests
            server_socket.settimeout(1.0)

            try:
                client_socket, addr = server_socket.accept()
                logger.info(f"Accepted connection from {addr}")
                self.handle_client(client_socket)
            except socket.timeout:
                pass
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                return

            response_body = "Hello from Substrato 0 HTTP Server!"
            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n\r\n"
            )
            response = response_headers + response_body
            client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    server = Substrato0HTTPServer()
    # To run indefinitely in a real scenario, use a while True loop in start.
    # We do a simple timeout for demonstration/testing.
    server.start()
