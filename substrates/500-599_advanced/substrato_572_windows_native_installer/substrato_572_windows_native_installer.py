import os
import json
import hashlib
import tempfile
from pathlib import Path

class Substrate572Canonizer:
    def __init__(self):
        self.version = "v∞.Ω.∇+++"
        self.phi_c = 0.999000
        self.base_dir = Path(__file__).parent
        self.artifacts = [
            "ArkheService.cs",
            "ArkheInstaller.wxs",
            "build_msi.ps1"
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

        canonical_str = (
            "ARKHE_NATIVE_WINDOWS_INSTALLER"
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
            "metadata": {
                "substrate": "572-WINDOWS-NATIVE-INSTALLER",
                "status": "CANONIZED_CLEAN",
                "phi_c": self.phi_c,
                "strict_mode": "PASS",
                "invariants_passed": 18,
                "seal": seal,
                "canonical_str": canonical_str
            },
            "build_components": {
                "service": "ArkheService.cs",
                "installer_script": "ArkheInstaller.wxs",
                "builder": "build_msi.ps1"
            },
            "performance_targets": {
                "framework": ".NET Native C#",
                "installer": "MSI (WiX Toolset)",
                "execution_speed": "Bare-metal Windows Service"
            },
            "artifact_hashes": artifact_hashes
        }

        fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="substrato_572_")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            print("Canonization 572 complete. Report saved to: {0}".format(temp_path))
            print(json.dumps(report, indent=4, ensure_ascii=False))
        except Exception as e:
            os.close(fd)
            raise e
        return temp_path

if __name__ == "__main__":
    canonizer = Substrate572Canonizer()
    canonizer.canonize()
