# ARKHE AGI Specification v2.0

## Nome
ARKHE General Intelligence Package (.agi)

## Versão
2.0

## Status
ESTÁVEL — Sujeito a extensão compatível

## Resumo
O formato .agi é o formato canônico de distribuição para substratos
do ARKHE Ω-TEMP. Um pacote .agi contém:
- Manifiesto canônico assinado
- Carga cifrada
- Prova de integridade Merkle
- Metadados de atestado TEE

## Formato Binário

### Header (9 bytes)
```
Offset  Size  Field         Type     Description
0       4     magic         uint32   0x00474149 ("\x00AGI")
4       2     version       uint16   Versão do formato (0x0002)
6       2     num_artifacts uint16   Número de artefatos no pacote
8       1     attestation   uint8    Tipo de atestado (0=none, 1=SGX, 2=SEV, 3=CCA)
```

| Campo       | Valor              |
|-------------|--------------------|
| magic       | `0x00474149`       |
| version     | `0x0002` (v2.0)    |
| attestation | `0`=Nenhum, `1`=SGX, `2`=SEV-SNP, `3`=ARM CCA |

### Chave de Cifragem (32 bytes)
```
Offset  Size  Field          Type   Description
9       32    wrapped_key    bytes  SHA3-256(chave_aes) — derivada via KDF do enclave
```

### Nonce (12 bytes)
```
Offset  Size  Field          Type   Description
41      12    nonce          bytes  Nonce AES-GCM
```

### Manifesto (variável)
```
Offset  Size  Field           Type    Description
53      4     manifest_len    uint32  Comprimento do manifesto JSON (BE)
57      N     manifest        bytes   JSON UTF-8 (consultar schema abaixo)
```

### Payload Cifrado (variável)
```
Offset  Size  Field             Type    Description
53+N    4     payload_len       uint32  Comprimento do payload cifrado (BE)
57+N    M     encrypted_payload bytes   Payload cifrado com AES-256-GCM
                                      Associated Data: nome do pacote (do manifesto)
```

### Merkle Proofs (variável)
Para cada artefato (na ordem do manifesto):
```
Formato por prova:
  2 bytes       proof_length
  proof_length  proof_bytes
    - Cada entrada da prova:
      1 byte     direction  (0x00=left, 0x01=right)
      32 bytes   sibling_hash (SHA3-256)
```

### Checksum do Pacote (32 bytes)
```
Últimos 32 bytes: SHA3-256 de todo o pacote (excluindo este campo)
```

## Estrutura do Manifesto JSON

```jsonc
{
  // Identificação
  "name": "string",           // Nome do pacote
  "version": "string",        // Versão semântica
  "substrate_id": 1,        // ID do substrato ARKHE

  // Autoridade
  "author": "string",         // Nome do autor/entidade
  "falcon_public_key": "base64",  // Chave pública Falcon-1024
  "falcon_signature": "base64",   // Assinatura sobre unsigned_hash

  // Integridade
  "sha3_256_manifest": "hex",     // Hash SHA3-256 DESTE manifesto (com assinatura)
  "unsigned_hash": "hex",         // Hash SHA3-256 do manifesto SEM assinatura
  "merkle_root": "hex",           // Raiz da Merkle tree dos artefatos

  // Criptografia
  "cipher": "AES-256-GCM",       // Algoritmo de cifragem
  "hash_algo": "SHA3-256",       // Algoritmo de hash
  "sig_algo": "FALCON-1024",     // Algoritmo de assinatura

  // Artefatos
  "artifacts": [
    {
      "id": "string",             // Identificador único
      "original_size": 1,       // Tamanho descomprimido
      "compressed_size": 1,     // Tamanho comprimido
      "sha3_256": "hex"           // Hash do artefato original (descomprimido)
    }
  ],

  // Atestado TEE
  "sgx_report": {                  // Obrigatório se attestation==SGX
    "mrenclave_hex": "hex",
    "mrsigner_hex": "hex",
    "measurement_hex": "hex",
    "report_data_hex": "hex",
    "timestamp": 1.0,
    "isvprodid": "hex",
    "isvsvn": 1,
    "type": "sgx-epid|sgx-dcap"
  },
  "sev_measurement": "hex",        // Obrigatório se attestation==SEV
  "cca_measurement": "hex",        // Obrigatório se attestation==CCA

  // Compatibilidade
  "dependencies": ["string"],      // Outros .agi necessários
  "entrypoint": "string",           // Ponto de entrada para execução

  // Timestamp
  "created_at": 1.0               // Unix timestamp
}
```

## Ordem de Verificação

Um loader AGI DEVE verificar, nesta ordem:

1. **Magic Number** — `package[0:4] == 0x00474149`
2. **Versão** — Suportar versão ≤ `package_version`
3. **Chave Pública** — Verificar se `author` está em `trusted_pubkeys`
4. **Hash do Manifesto** — `SHA3-256(manifest_raw) == sha3_256_manifest`
   - Se falhar: tentar `SHA3-256(manifest_without_signature) == unsigned_hash`

5. **Assinatura Falcon-1024** — Assinar `SHA3-256(manifest_without_signature)` com chave autorizada
6. **Atestado TEE** — Se presente, verificar MRENCLAVE/MEDIGEST
7. **Decifrar Payload** — `AES-256-GCM.decrypt(nonce, encrypted, associated_data=package_name)`
8. **Merkle Proofs** — Para cada artefato, verificar prova contra merkle_root
9. **SHA3-256 de Artefatos** — Verificar hash individual de cada artefato

## Algoritmos Criptográficos

| Componente      | Algoritmo                | Tamanho     |
|-----------------|--------------------------|-------------|
| Hash            | SHA3-256 (FIPS 202)      | 256 bits    |
| Assinatura      | Falcon-1024 (ML-DSA)     | ~1280 bytes |
| Chave Pública   | Falcon-1024              | 1792 bytes  |
| Chave Secreta   | Falcon-1024              | 3584 bytes  |
| Cifragem        | AES-256-GCM (NIST SP 800-38D) | 256 bits key |
| Compressão      | ZSTD (nível 19) / zlib (nível 9) | — |
| Tree            | Merkle SHA3-256          | 256-bit leaves |

## Extensões Futuras

- v3.0: Suporte a múltiplas assinaturas (threshold signatures)
- v3.0: Suporte a ZK-SNARK proofs embarcados
- v3.0: Suporte a atualizações delta (diferencial em relação a versão anterior)
- v4.0: Streaming de payload (para pacotes > 1GB)
