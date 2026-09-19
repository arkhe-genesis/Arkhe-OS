"""Generate canonical JSON routing manifests."""
import json
import blake3

def compute_hash(manifest: dict) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return blake3.blake3(payload).hexdigest()
def generate_manifest(experts, routing_table_hash, governance):
    manifest={"arkhe_version":"1.0.0","manifest_type":"routing_manifest","moe":{"total_experts":len(experts),"active_experts_per_token":4,"routing_table_hash":routing_table_hash,"expert_manifest":[{"index":e["id"],"cid":e.get("cid",""),"country":e["country"],"size_bytes":e.get("size_bytes",0)} for e in experts]},"brics_governance":governance,"brics_invariants":["INV-BRICS-01","INV-BRICS-02","INV-BRICS-04","INV-BRICS-05"],"arkhe_identity":{"did":"did:cid:pending","signature":{"ed25519":"pending","ml_dsa_65":"pending"}},"arkhe_rekor_entry_id":None}
    manifest["arkhe_record_hash"] = compute_hash(manifest)
    return manifest
