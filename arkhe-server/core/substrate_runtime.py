class SubstrateRuntime:
    def __init__(self):
        self.substrates = {}

    def register(self, name, substrate):
        self.substrates[name] = substrate

    def execute(self, name, *args, **kwargs):
        if name in self.substrates:
            return self.substrates[name].run(*args, **kwargs)
        raise ValueError(f"Substrate {name} not found")

def execute_substrate():
    runtime = SubstrateRuntime()
    return runtime

if __name__ == "__main__":
    print("Starting Substrate Runtime")
    execute_substrate()
