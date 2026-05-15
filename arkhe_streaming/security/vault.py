import json
import logging

class CredentialsVault:
    def __init__(self):
        self._vault = {}
        logging.info("CredentialsVault initialized.")

    def store_token(self, platform: str, token: str):
        self._vault[platform] = token

    def get_token(self, platform: str) -> str:
        return self._vault.get(platform, "")

class OAuth2Client:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        logging.info(f"OAuth2Client initialized for client_id: {client_id}")

    def fetch_credentials(self, platform: str) -> str:
        # Mock fetching credentials
        return f"mock_oauth_token_for_{platform}_{self.client_id}"
