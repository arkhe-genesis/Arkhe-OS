import time

class Substrato4RateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        """
        Token Bucket Rate Limiter
        :param capacity: Maximum number of tokens in the bucket
        :param refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill_time = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill_time
        tokens_to_add = elapsed * self.refill_rate

        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill_time = now

    def allow_request(self) -> bool:
        """Checks if a request is allowed based on available tokens."""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

if __name__ == "__main__":
    limiter = Substrato4RateLimiter(capacity=3, refill_rate=1.0)
    for i in range(5):
        if limiter.allow_request():
            print(f"Request {i+1} allowed")
        else:
            print(f"Request {i+1} denied")

    print("Waiting 2 seconds...")
    time.sleep(2)
    if limiter.allow_request():
        print("Request after wait allowed")
