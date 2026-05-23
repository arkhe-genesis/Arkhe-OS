import json
import hashlib
import time

class NIP34Governance:
    """
    Models the NIP-34 protocol as an alternative to TemporalChain
    for registering governance decisions (with final anchor on chain).
    """
    def __init__(self):
        self.relays = ["wss://relay.damus.io"]
        self.proposals = {}

    def propose(self, patch_content, author_npub):
        """
        Propose a governance decision or patch as a NIP-34 event.
        """
        combined = "{}{}{}".format(author_npub, patch_content, time.time())
        proposal_id = hashlib.sha256(combined.encode()).hexdigest()
        event = {
            "kind": 1621, # NIP-34 patch proposal
            "id": proposal_id,
            "pubkey": author_npub,
            "created_at": int(time.time()),
            "tags": [["a", "30023:npub...:article"]],
            "content": patch_content,
            "sig": "simulated_signature"
        }
        self.proposals[proposal_id] = event
        # Publish to relays...
        return proposal_id

    def merge(self, proposal_id, merger_npub):
        """
        Accept a NIP-34 patch.
        """
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")

        combined = "merge{}".format(proposal_id)
        event = {
            "kind": 1622, # NIP-34 patch acceptance
            "id": hashlib.sha256(combined.encode()).hexdigest(),
            "pubkey": merger_npub,
            "created_at": int(time.time()),
            "tags": [["e", proposal_id, self.relays[0], "reply"]],
            "content": "Merged.",
            "sig": "simulated_signature"
        }
        return event

    def anchor(self, proposal_id, chain_oracle):
        """
        Anchor the merged NIP-34 governance decision to the TemporalChain.
        """
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")

        proposal_hash = self.proposals[proposal_id]["id"]
        # Simulate anchoring to TemporalChain
        anchor_receipt = chain_oracle.anchor_data({"type": "NIP-34-Governance", "proposal_hash": proposal_hash})
        return anchor_receipt
