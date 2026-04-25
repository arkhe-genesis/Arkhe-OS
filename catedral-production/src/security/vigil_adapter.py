class VigilAdapter:
    def __init__(self, config=None):
        self.mode = "active"
    def set_mode(self, mode):
        self.mode = mode
        return True
