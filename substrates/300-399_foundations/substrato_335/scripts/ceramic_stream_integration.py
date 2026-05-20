import json
import time
from datetime import datetime

# =============================================================================
# CERAMIC INTEGRATION MOCK - ORKUT 2.0 (Substrato 335)
# =============================================================================
# In a real environment, this connects to a Ceramic node via the HTTP API or
# ComposeDB to manage mutable identity streams (TileDocuments/ModelInstanceDocuments)
# while interacting with the smart contracts.

class CeramicMockClient:
    def __init__(self, endpoint="https://ceramic-clay.3boxlabs.com"):
        self.endpoint = endpoint
        self.streams = {}
        print(f"[{datetime.now().isoformat()}] Initialized Ceramic Node connection at {self.endpoint}")

    def create_profile_stream(self, orcid: str, metadata: dict) -> str:
        """Creates a Ceramic TileDocument for the Researcher Profile."""
        stream_id = f"ceramic://kjzl6cwe1jw14{int(time.time())}"
        self.streams[stream_id] = {
            "orcid": orcid,
            "content": metadata,
            "schema": "ceramic://orkut2_profile_schema_v1",
            "commits": 1
        }
        print(f"[Ceramic] Profile stream created: {stream_id}")
        return stream_id

    def update_profile_stream(self, stream_id: str, new_metadata: dict) -> bool:
        """Appends a new commit to the mutable Profile Stream."""
        if stream_id not in self.streams:
            print(f"[Ceramic Error] Stream {stream_id} not found.")
            return False

        self.streams[stream_id]["content"].update(new_metadata)
        self.streams[stream_id]["commits"] += 1
        print(f"[Ceramic] Profile stream {stream_id} updated (Commit {self.streams[stream_id]['commits']})")
        return True

    def get_profile_stream(self, stream_id: str) -> dict:
        return self.streams.get(stream_id, {})

if __name__ == "__main__":
    client = CeramicMockClient()

    # 1. User Authenticates via Arkhe Wallet + ORCID
    orcid = "0000-0002-1825-0097"

    # 2. Setup initial rich metadata for Orkut 2.0 Profile
    metadata = {
        "name": "Dra. Elara Vance",
        "institution": "Arkhe Institute of Photonic Anomalies",
        "bio": "Pesquisadora na interseção de fônons e consciências distribuídas.",
        "communities": ["Biofotônica", "Física de Matéria Condensada"],
        "badges": ["Primeiro Scrap Ancorado", "Autora Vivo"]
    }

    # 3. Create mutable stream on Ceramic
    stream_id = client.create_profile_stream(orcid, metadata)

    # 4. User updates their bio later
    client.update_profile_stream(stream_id, {"bio": "Pesquisadora sênior na Catedral. Foco em VDF."})

    # 5. Retrieve final stream state
    final_state = client.get_profile_stream(stream_id)
    print("\nFinal Stream State on Ceramic:")
    print(json.dumps(final_state, indent=2))
