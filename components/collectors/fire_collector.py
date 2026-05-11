#!/usr/bin/env python3
import requests, redis, json, time, os
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
def main():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    while True:
        try:
            clusters = [{"lat": -10.0, "lon": -50.0, "intensity": 350.0}]
            r.xadd("akasha:eco:firms", {"clusters": json.dumps(clusters)}, maxlen=5000)
        except Exception as e: print(f"[Fire] Error: {e}")
        time.sleep(14400)
if __name__ == "__main__": main()
