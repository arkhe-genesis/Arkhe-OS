import asyncio
import json
import time

# Dummy class for Producer
class Producer:
    def __init__(self, conf):
        pass

    def produce(self, topic, key, value, callback):
        pass

    def flush(self):
        pass

async def generate_load(messages_per_second: int, duration_seconds: int):
    """Gera carga de teste para o pipeline Spark."""
    conf = {'bootstrap.servers': 'kafka.arkhe:9092'}
    producer = Producer(conf)

    total_messages = messages_per_second * duration_seconds
    start_time = time.time()

    for i in range(total_messages):
        message = {
            "stream_id": f"load_test_{i % 100}",
            "platform": "twitch",
            "message": f"load_message_{i}",
            "chatter": f"user_{i % 1000}",
            "safe": True,
            "timestamp": time.time(),
        }

        producer.produce(
            "chat_messages",
            key=f"load_test_{i % 100}",
            value=json.dumps(message),
            callback=lambda err, msg: None
        )

        # Controlar rate
        if i % messages_per_second == 0 and i > 0:
            producer.flush()
            elapsed = time.time() - start_time
            expected = i / messages_per_second
            if elapsed < expected:
                await asyncio.sleep(expected - elapsed)

    producer.flush()
    print(f"✅ Load test completo: {total_messages} mensagens em {time.time() - start_time:.1f}s")

if __name__ == "__main__":
    asyncio.run(generate_load(10000, 60))
