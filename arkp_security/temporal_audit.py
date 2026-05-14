class TemporalAuditLogger:
    @staticmethod
    async def query(filter, limit, offset, mask_pii):
        class Results:
            def __init__(self):
                self.total = 0
                self.items = []
        return Results()

    @staticmethod
    async def get_by_seal(seal):
        return None
