#!/usr/bin/env python3
import requests, redis, json, time, csv, io, os
GDELT_UPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
def main():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    while True:
        try:
            resp = requests.get(GDELT_UPDATE_URL, timeout=10).text.strip().split('\n')
            url = resp[2].split(' ')[2]
            with requests.get(url, stream=True, timeout=30) as r_csv:
                raw = io.StringIO()
                for i, line in enumerate(r_csv.iter_lines(decode_unicode=True)):
                    if i > 1000: break
                    raw.write(line + '\n')
                raw.seek(0)
                reader = csv.reader(raw, delimiter='\t')
                events = []
                for row in reader:
                    if len(row) < 42: continue
                    if row[26].startswith('14'):
                        events.append({"type": "social_unrest", "tone": float(row[34]) if row[34] else 0.0})
                if events:
                    r.xadd("akasha:soc:gdelt", {"events": json.dumps(events)}, maxlen=10000)
        except: pass
        time.sleep(900)
if __name__ == "__main__": main()
