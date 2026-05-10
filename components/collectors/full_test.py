import redis, json, time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def test_communication():
    print("Testing Redis communication...")
    try:
        r.set("test_key", "active")
        val = r.get("test_key")
        print(f"Redis link: {val}")

        # Test stream
        r.xadd("test_stream", {"msg": "hello"})
        msgs = r.xread({"test_stream": 0})
        print(f"Stream link: {len(msgs)} messages")
        return True
    except Exception as e:
        print(f"Communication failed: {e}")
        return False

if __name__ == "__main__":
    if test_communication():
        print("Backend communication logic verified.")
    else:
        exit(1)
