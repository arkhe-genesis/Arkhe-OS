class TemporalChain:
    def __init__(self, endpoint=None):
        self.current_seal = "mock_seal"
    async def anchor_event(self, event_type, payload):
        pass
