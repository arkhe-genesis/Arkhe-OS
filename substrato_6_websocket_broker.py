from collections import defaultdict
from typing import Set

class Substrato6WebsocketBroker:
    def __init__(self):
        # channel -> set of client connections (simulated by client IDs here)
        self.channels = defaultdict(set)

    def subscribe(self, client_id: str, channel: str):
        """Subscribes a client to a channel."""
        self.channels[channel].add(client_id)
        print(f"Client {client_id} subscribed to {channel}")

    def unsubscribe(self, client_id: str, channel: str):
        """Unsubscribes a client from a channel."""
        if channel in self.channels and client_id in self.channels[channel]:
            self.channels[channel].remove(client_id)
            print(f"Client {client_id} unsubscribed from {channel}")

    def publish(self, channel: str, message: str):
        """Publishes a message to all clients in a channel."""
        if channel in self.channels:
            for client_id in self.channels[channel]:
                # Simulate sending message over a websocket connection
                self._send_to_client(client_id, message)

    def _send_to_client(self, client_id: str, message: str):
        print(f"[WS] Sending to {client_id}: {message}")

if __name__ == "__main__":
    broker = Substrato6WebsocketBroker()
    broker.subscribe("client_1", "chat_room")
    broker.subscribe("client_2", "chat_room")
    broker.subscribe("client_3", "alerts")

    broker.publish("chat_room", "Hello everyone!")
    broker.publish("alerts", "System going down for maintenance.")

    broker.unsubscribe("client_1", "chat_room")
    broker.publish("chat_room", "Client 1 left.")
