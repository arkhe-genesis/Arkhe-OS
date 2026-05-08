import json, tarfile

def view_manifest(path: str):
    """View MANIFEST.json from .agi artifact."""
    with tarfile.open(path, 'r:*') as tar:
        manifest = json.loads(tar.extractfile('MANIFEST.json').read())
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
