"""
Mock OrcidAuthProvider
"""
from dataclasses import dataclass

@dataclass
class OrcidIdentity:
    orcid: str

class OrcidAuthProvider:
    def get_identity(self, auth_token: str):
        if auth_token:
            return OrcidIdentity(orcid="0000-0000-0000-0000")
        return None
