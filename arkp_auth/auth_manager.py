class AuthManager:
    def verify_token(self, token):
        # Mock token verification
        if token:
            return {"sub": "0009-0005-2697-4668"}
        return None

class ORCIDClaim:
    pass
