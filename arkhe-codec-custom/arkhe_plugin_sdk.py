class ArkhePluginBase:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def execute_pipeline(self, state_registry_ref) -> dict:
        raise NotImplementedError("Plugins must implement execute_pipeline()")
