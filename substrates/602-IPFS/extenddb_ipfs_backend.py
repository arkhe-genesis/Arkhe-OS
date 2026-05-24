class ExtendDBIPFSBackend:
    def __init__(self, ipfs_bridge):
        self.bridge = ipfs_bridge

    def resolve(self, cid):
        return self.bridge.get_cid(cid)
