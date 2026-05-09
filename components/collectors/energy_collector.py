#!/usr/bin/env python3
import requests, redis, json, time, os
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
def main():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    zones = ["BR-CS", "US-CAL", "DE"]
    while True:
        for zone in zones:
            event = {"type": "energy", "zone": zone, "carbon_intensity": 400, "renewable_percentage": 45.0}
            r.xadd("akasha:infra:energy", {"event": json.dumps(event)}, maxlen=10000)
        time.sleep(900)
if __name__ == "__main__": main()
