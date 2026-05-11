import hashlib
class ONNXModelRegistry:
    def __init__(self, storage_dir=None):
        pass
    def register_model(self, onnx_path, publisher_seal, phi_c_training, datasets, license_type, signature):
        with open(onnx_path, "rb") as f:
            return hashlib.sha3_256(f.read()).hexdigest()
    def load_session(self, h):
        return True

class ONNXModelEntry:
    pass
