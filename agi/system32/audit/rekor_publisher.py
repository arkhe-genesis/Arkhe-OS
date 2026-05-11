class RekorPublisher:
    def __init__(self, url, mock_requests=False):
        self.url = url
    def publish(self, p):
        return "dummy_uuid"
    def publish_proof(self, p, d):
        return type('Entry', (), {'rekor_uuid': 'mock_uuid_123'})()
