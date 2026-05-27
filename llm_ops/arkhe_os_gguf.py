import hashlib

class ArkheOSGGUF:
    def __init__(self, name):
        self.name = name
        self.metadata = {}
        self.tensors = []

    def set_metadata(self, key, value):
        self.metadata[key] = value

    def add_tensor(self, name, shape, dtype, offset):
        self.tensors.append({"name": name, "shape": shape, "dtype": dtype, "offset": offset})

    def to_gguf_binary(self):
        # mock implementation returning bytes
        data = f"GGUF_MOCK_{self.name}".encode('utf-8')
        return data

    def compute_checksum(self):
        return hashlib.sha3_256(self.to_gguf_binary()).hexdigest()
