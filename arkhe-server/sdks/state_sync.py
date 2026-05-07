class StateSync:
    def sync_qhttp(self, url):
        return f"Synced with {url} via qhttp"

    def emit_nostr_event(self, kind, content):
        return {"kind": kind, "content": content}

def sync_state():
    sync = StateSync()
    return sync
