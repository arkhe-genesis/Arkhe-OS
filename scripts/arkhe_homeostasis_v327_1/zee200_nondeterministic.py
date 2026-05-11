class NonDeterministicProofSeed:
    def __init__(self, entropy_sources, chain_binding):
        self.entropy_sources = entropy_sources
        self.chain_binding = chain_binding
