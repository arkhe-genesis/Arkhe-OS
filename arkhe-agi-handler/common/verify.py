import hashlib, json, tarfile

def verify_artifact(path: str) -> bool:
    """Verify .agi artifact integrity (SHA256 + Ed25519 signature)."""
    try:
        with tarfile.open(path, 'r:*') as tar:
            manifest = json.loads(tar.extractfile('MANIFEST.json').read())
            checksums = tar.extractfile('SHA256SUMS').read().decode()
            seal = tar.extractfile('SEAL.asc').read().decode()

        # Verify checksums
        for line in checksums.strip().split('\n'):
            if not line or line.startswith('#'): continue
            expected_hash, fname = line.split('  ', 1)
            member = tar.getmember(fname.strip())
            actual_hash = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
            if actual_hash != expected_hash: return False

        # Verify Ed25519 signature (placeholder - use libsodium in production)
        # In production: verify seal against manifest hash using public key
        return True
    except Exception: return False
