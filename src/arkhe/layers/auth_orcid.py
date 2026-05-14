"""
Mock OrcidAuthProvider
"""
from dataclasses import dataclass

@dataclass
class OrcidIdentity:
    orcid: str

class OrcidAuthProvider:
    def __init__(self):
        self.identities = {}

    def register(self, orcid: str, token: str):
        self.identities[token] = orcid
        return OrcidIdentity(orcid=orcid)

    def get_identity(self, auth_token: str):
        if auth_token in self.identities:
            return OrcidIdentity(orcid=self.identities[auth_token])
        if auth_token:
            return OrcidIdentity(orcid="0000-0000-0000-0000")
        return None
