#!/usr/bin/env python3
import requests, redis, json, time, os
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
def main():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    while True:
        try:
            data = requests.get(USGS_URL, timeout=15).json()
            for f in data.get('features', []):
                p, g = f['properties'], f['geometry']
                event = {"type": "earthquake", "magnitude": p.get('mag', 0), "place": p.get('place', "Unknown"), "coords": g.get('coordinates')}
                r.xadd("akasha:geo:earthquakes", {"event": json.dumps(event)}, maxlen=10000)
        except Exception as e: print(f"[Geo] Error: {e}")
        time.sleep(300)
if __name__ == "__main__": main()
