import tarfile
from pathlib import Path

def extract_artifact(path: str, output: str):
    """Extract .agi artifact to output directory."""
    Path(output).mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, 'r:*') as tar:
        tar.extractall(path=output, members=[m for m in tar if m.name not in ['SHA256SUMS', 'SEAL.asc']])
