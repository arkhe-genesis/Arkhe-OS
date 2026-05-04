import json

registry = {
  "octra_endpoint": "octra://arkhe.cosmicdao.network",
  "protocol_version": "OCTRA-v1",
  "total_proofs": 8,
  "registry": [
    {
      "octra_tx_id": "166e2c88613047206ef1e8a42db2d9a8",
      "commitment": "82710e257a678bc3641f9c473e05c7d32d1c4bd2a64376adfa01edf67f90c018",
      "timestamp_registered": 1777738578475785182,
      "status": "confirmed",
      "block_height": 1,
      "merkle_root": "82710e257a678bc3641f9c473e05c7d32d1c4bd2a64376adfa01edf67f90c018"
    },
    {
      "octra_tx_id": "61d0b8a537df2556dc9c7b7a5a9e6ca2",
      "commitment": "7594df70446935a9c9bdfb18f5e761fae73b028295cb7697cf88bdf1a12adef2",
      "timestamp_registered": 1777738578475932830,
      "status": "confirmed",
      "block_height": 2,
      "merkle_root": "7594df70446935a9c9bdfb18f5e761fae73b028295cb7697cf88bdf1a12adef2"
    },
    {
      "octra_tx_id": "396aaf89c3f68967897a76b7b9f51f00",
      "commitment": "ff7a6ecd1741f7a78af13c5e85907aa6be6f57d95fad6b0f4015c374ae7860a4",
      "timestamp_registered": 1777738578476043024,
      "status": "confirmed",
      "block_height": 3,
      "merkle_root": "ff7a6ecd1741f7a78af13c5e85907aa6be6f57d95fad6b0f4015c374ae7860a4"
    },
    {
      "octra_tx_id": "aaea11e3763d3ec882baa0c561d65bf8",
      "commitment": "a159184f6a0c379964dfec925f37e8825b7b7435743d6751eb28a386c33474af",
      "timestamp_registered": 1777738578476150081,
      "status": "confirmed",
      "block_height": 4,
      "merkle_root": "a159184f6a0c379964dfec925f37e8825b7b7435743d6751eb28a386c33474af"
    },
    {
      "octra_tx_id": "f70180574be622a98ee9b983ffd2152e",
      "commitment": "57eee0d817e49ce41ccef93a453028c4ed0c36930128ae6a55872534815eb94d",
      "timestamp_registered": 1777738578476244583,
      "status": "confirmed",
      "block_height": 5,
      "merkle_root": "57eee0d817e49ce41ccef93a453028c4ed0c36930128ae6a55872534815eb94d"
    },
    {
      "octra_tx_id": "11e4a135f5ef841493bb47b8d0291dd7",
      "commitment": "aa6c9dceb94828c51fdcc02d2074f6786a6d2cc34807978882a89b80b4ab984a",
      "timestamp_registered": 1777738578476334276,
      "status": "confirmed",
      "block_height": 6,
      "merkle_root": "aa6c9dceb94828c51fdcc02d2074f6786a6d2cc34807978882a89b80b4ab984a"
    },
    {
      "octra_tx_id": "f97dc72f84af21b5ba3782201b9f42e3",
      "commitment": "1e13e46c80437644e120d2373778ff28a5bc870f6487810a8dff838ebedd9bb1",
      "timestamp_registered": 1777738578476436742,
      "status": "confirmed",
      "block_height": 7,
      "merkle_root": "1e13e46c80437644e120d2373778ff28a5bc870f6487810a8dff838ebedd9bb1"
    },
    {
      "octra_tx_id": "047247828b23491f36a454bb9ec17721",
      "commitment": "4446d5ea0452f6988999590523de6b120489fc24b7ca64351fbc7feae3819c12",
      "timestamp_registered": 1777738578476527733,
      "status": "confirmed",
      "block_height": 8,
      "merkle_root": "4446d5ea0452f6988999590523de6b120489fc24b7ca64351fbc7feae3819c12"
    }
  ],
  "timestamp": "2026-05-03T00:16:18.476670",
  "architect": "Rafael Oliveira",
  "orcid": "0009-0005-2697-4668"
}

with open("arkhe-v3277/results/octra/octra_registry.json", "w") as f:
    json.dump(registry, f, indent=2)

print("Exporting complete registry...")
