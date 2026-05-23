import os
import json
import hashlib
import tempfile
from pathlib import Path

class WindowsPortCanonizer:
    def __init__(self):
        self.version = "v∞.Ω.∇+++"
        self.phi_c = 0.990278
        self.base_dir = Path(__file__).parent
        self.artifacts = [
            "Dockerfile.windows",
            "docker-compose.windows.yml",
            "verify_constitution_windows.py",
            "ArkheBridgeService.py",
            "Install-ArkheWindows.ps1"
        ]

    def _calculate_artifact_hashes(self):
        hashes = {}
        for artifact in self.artifacts:
            path = self.base_dir / artifact
            if path.exists():
                content = path.read_bytes()
                hashes[artifact] = hashlib.sha256(content).hexdigest()
            else:
                hashes[artifact] = "MISSING"
        return hashes

    def canonize(self):
        artifact_hashes = self._calculate_artifact_hashes()

        # Use exact canonical string per instructions
        canonical_str = (
            "ARKHE_WINDOWS_PORT"
            "_{0}"
            "_PHI_C:{1:.6f}"
            "_ARTIFACTS:{2}"
        ).format(
            self.version,
            self.phi_c,
            ",".join(sorted(self.artifacts))
        )

        seal = hashlib.sha3_256(canonical_str.encode('utf-8')).hexdigest()

        report = {
            "module": "ARKHE Ω‑TEMP WINDOWS PORT",
            "version": self.version,
            "vias": {
                "Via_I": {
                    "technology": "WSL2 + Docker Desktop",
                    "preservation": "100%",
                    "description": "WSL2 kernel Linux 5.15+, Docker Desktop Windows"
                },
                "Via_II": {
                    "technology": "Windows Container Nativo",
                    "preservation": "~85%",
                    "description": "Windows Server puro, datacenter"
                },
                "Via_III": {
                    "technology": "Native Windows Service",
                    "preservation": "~80%",
                    "description": "Python 3.12 + pywin32 serviço"
                }
            },
            "artifacts": artifact_hashes,
            "phi_c": self.phi_c,
            "canonical_str": canonical_str,
            "seal_sha3_256": seal
        }

        fd, temp_path = tempfile.mkstemp(suffix=".json", text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            print("Canonization complete. Report saved to: {0}".format(temp_path))
            print(json.dumps(report, indent=4, ensure_ascii=False))
        except Exception as e:
            os.close(fd)
            raise e
        return temp_path

if __name__ == "__main__":
    canonizer = WindowsPortCanonizer()
    canonizer.canonize()
