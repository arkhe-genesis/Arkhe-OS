import json
import hashlib
import tempfile
import os

class ArkheContainerCanonizer:
    def canonize(self) -> str:
        data = {
            "metadata": {
                "substrate": "ARKHE-CONTAINER",
                "version": "1.0.0",
                "base": "Debian Bookworm (slim)",
                "layers": 6,
                "substrates_included": ["227-F (PCB)", "233 (Lagrangiano)"],
                "policies": ["seccomp-bpf", "SELinux", "capabilities drop", "cgroups"],
                "verification": ["eBPF probes", "proof packets SHA-3", "logs append-only"],
                "entrypoint": "arkhe_cli.py",
                "commands": ["verify", "227f", "233"],
                "healthcheck": "Hash verification de substratos"
            }
        }

        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        seal = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        data["metadata"]["seal"] = seal

        fd, path = tempfile.mkstemp(suffix=".json", text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path

if __name__ == '__main__':
    canonizer = ArkheContainerCanonizer()
    path = canonizer.canonize()
    print("Canonized output saved to: " + path)
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read())
