#!/usr/bin/env python3
import asyncio, websockets, json, redis, os, random
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
async def main():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    while True:
        event = {"type": "vessel_sim", "mmsi": random.randint(100, 999), "speed": random.uniform(0, 20)}
        r.xadd("akasha:mari:vessels", {"vessel": json.dumps(event)}, maxlen=10000)
        await asyncio.sleep(10)
if __name__ == "__main__": asyncio.run(main())
