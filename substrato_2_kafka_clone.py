from collections import defaultdict
from typing import List, Dict

class Substrato2KafkaClone:
    def __init__(self):
        # topic -> list of messages (append-only log)
        self.topics: Dict[str, List[str]] = defaultdict(list)
        # consumer_group -> topic -> offset
        self.consumer_offsets: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def produce(self, topic: str, message: str):
        """Appends a message to the specified topic."""
        self.topics[topic].append(message)

    def consume(self, topic: str, consumer_group: str) -> str:
        """Consumes the next message for a given consumer group on a topic."""
        if topic not in self.topics:
            return None

        offset = self.consumer_offsets[consumer_group][topic]
        if offset < len(self.topics[topic]):
            message = self.topics[topic][offset]
            self.consumer_offsets[consumer_group][topic] += 1
            return message
        return None

if __name__ == "__main__":
    kafka = Substrato2KafkaClone()
    kafka.produce("events", "event_1")
    kafka.produce("events", "event_2")
    print(kafka.consume("events", "group_A"))
    print(kafka.consume("events", "group_A"))
    print(kafka.consume("events", "group_A"))
    print(kafka.consume("events", "group_B"))
