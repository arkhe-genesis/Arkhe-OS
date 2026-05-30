import hashlib
import json

class OpenMDWLicense:
    def __init__(self, version="1.1"):
        self.version = version

    def verify_license(self, model_materials):
        # Simulates checking if model materials comply with OpenMDW v1.1
        hash_obj = hashlib.sha3_256(json.dumps(model_materials, sort_keys=True).encode("utf-8"))
        license_hash = hash_obj.hexdigest()
        return {
            "compliant": True,
            "version": self.version,
            "license_hash": license_hash
        }

class FCRSimulatorBridge:
    def __init__(self, license_manager):
        self.license_manager = license_manager

    def inject_fcr_output(self, slot, engine_name, model_materials):
        license_info = self.license_manager.verify_license(model_materials)
        if not license_info.get("compliant"):
            raise ValueError("Model materials do not comply with OpenMDW license.")

        return {
            "slot": slot,
            "engine_name": engine_name,
            "fast_confirmed": True,
            "license_hash": license_info.get("license_hash")
        }

if __name__ == "__main__":
    license_mgr = OpenMDWLicense()
    bridge = FCRSimulatorBridge(license_mgr)

    mock_materials = {"model_weights": "compliant", "documentation": "cc-by-4.0"}
    output = bridge.inject_fcr_output(slot=435000, engine_name="lighthouse", model_materials=mock_materials)
    print(json.dumps(output, indent=2))
