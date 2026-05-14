import hashlib
from src.arkhe.layers.ecosystem_arkp import Registry, ArtBlock
from src.arkhe.layers.package_ecosystem_addons import DependencyCache, SemVer

reg = Registry()
for name, ver in [("lib", "1.0.1"), ("lib", "1.1.0"), ("lib", "2.0.0")]:
    block = ArtBlock(block_id=hashlib.sha3_256(f"{name}:{ver}".encode()).hexdigest()[:16],
                     name=name, version=ver, manifest_hash="mhash", code_hash="chash", zk_proof=hashlib.sha3_256(f"{name}:{ver}:mhash:chash".encode()).hexdigest()[:16], temporal_anchor="tanchor")
    reg.publish(block)

print("Registry list_packages:", reg.list_packages())
print("Registry packages['lib'] versions:", [b.version for b in reg.packages.get("lib", [])])

cache = DependencyCache()
latest = cache.resolve_latest("lib", reg)
print("Latest lib version resolved by cache:", str(latest) if latest else "None")
