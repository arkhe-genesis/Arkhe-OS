class MRCController:
    def __init__(self):
        self.profiles = {}

    def load_profile(self, name, profile):
        self.profiles[name] = profile

    def run_probe(self, target):
        return {"target": target, "status": "probe_success"}

def control_mrc():
    controller = MRCController()
    return controller
