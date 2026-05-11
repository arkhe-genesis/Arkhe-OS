// ============================================================================
// ARKHE Ω-TEMP — SHA3-256 via WebCrypto API
// ============================================================================
// Utiliza a API nativa do browser para máxima performance.
// Fallback para implementação pura em caso de indisponibilidade.
// ============================================================================

export async function keccak256(data: BufferSource): Promise<Uint8Array> {
  try {
    const hashBuffer = await crypto.subtle.digest('SHA-3_256', data);
    return new Uint8Array(hashBuffer);
  } catch (e) {
    return keccak256Sync(typeof data === 'string' ? new TextEncoder().encode(data) : new Uint8Array(data as ArrayBuffer));
  }
}

export function keccak256Sync(data: Uint8Array): Uint8Array {
  const RATE_BYTES = 136;
  const RC: bigint[] = [0x0000000000000001n, 0x0000000000008082n, 0x800000000000808An, 0x8000000080008000n, 0x000000000000808Bn, 0x0000000080000001n, 0x8000000080008081n, 0x8000000000008009n, 0x000000000000008An, 0x0000000000000088n, 0x0000000080008009n, 0x000000008000000An, 0x0000000080008081n, 0x8000000000008080n, 0x0000000000000001n, 0x8000000080008008n];
  const RHO = [0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14];
  const PI = [0,6,12,18,24,3,9,10,16,22,1,7,13,19,20,4,5,11,17,23,2,8,14,15,21];

  const state: bigint[] = new Array(25).fill(0n);
  const input = data;
  let offset = 0;

  while (offset + RATE_BYTES <= input.length) {
    for (let i = 0; i < RATE_BYTES; i += 8) {
      let word = 0n;
      for (let j = 0; j < 8; j++) word |= BigInt(input[offset + i + j]) << (BigInt(j) * 8n);
      state[i / 8] ^= word;
    }
    keccakF1600(state, RC);
    offset += RATE_BYTES;
  }

  const remaining = input.length - offset;
  const block = new Uint8Array(RATE_BYTES);
  block.set(input.slice(offset));
  if (remaining < RATE_BYTES - 1) { block[remaining] = 0x06; block[RATE_BYTES - 1] = 0x80; }
  else { block[remaining] = 0x06; keccakF1600(state, RC); block.fill(0); block[RATE_BYTES - 1] = 0x80; }

  for (let i = 0; i < RATE_BYTES; i += 8) {
    let word = 0n;
    for (let j = 0; j < 8; j++) word |= BigInt(block[i + j]) << (BigInt(j) * 8n);
    state[i / 8] ^= word;
  }
  keccakF1600(state, RC);

  const output = new Uint8Array(32);
  for (let i = 0; i < 4; i++) {
    const word = state[i];
    for (let j = 0; j < 8; j++) output[i * 8 + j] = Number((word >> (BigInt(j) * 8n)) & 0xFFn);
  }
  return output;
}

function rotl64(x: bigint, n: bigint): bigint { n = n % 64n; return ((x << n) | (x >> (64n - n))) & 0xFFFFFFFFFFFFFFFFn; }

function keccakF1600(state: bigint[], rc: bigint[]): void {
  const RHO = [0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14];
  const PI = [0,6,12,18,24,3,9,10,16,22,1,7,13,19,20,4,5,11,17,23,2,8,14,15,21];

  for (let round = 0; round < 24; round++) {
    const C: bigint[] = [];
    for (let x = 0; x < 5; x++) C[x] = state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20];
    const D: bigint[] = [];
    for (let x = 0; x < 5; x++) D[x] = C[(x + 4) % 5] ^ rotl64(C[(x + 1) % 5], 1n);
    for (let x = 0; x < 5; x++) for (let y = 0; y < 5; y++) state[x + 5 * y] ^= D[x];

    const B: bigint[] = [];
    for (let x = 0; x < 5; x++) for (let y = 0; y < 5; y++) B[PI[x + 5 * y]] = rotl64(state[x + 5 * y], BigInt(RHO[x + 5 * y]));
    for (let i = 0; i < 25; i++) state[i] = B[i];

    for (let y = 0; y < 5; y++) {
      const row: bigint[] = [];
      for (let x = 0; x < 5; x++) row.push(state[x + 5 * y]);
      for (let x = 0; x < 5; x++) state[x + 5 * y] = row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5]);
    }

    state[0] ^= rc[round];
  }
}

export function keccak256Empty(): Uint8Array {
  const block = new Uint8Array(136);
  block[0] = 0x06;
  block[135] = 0x80;
  const state: bigint[] = new Array(25).fill(0n);
  for (let i = 0; i < 136; i += 8) {
    let word = 0n;
    for (let j = 0; j < 8; j++) word |= BigInt(block[i + j]) << (BigInt(j) * 8n);
    state[i / 8] ^= word;
  }
  keccakF1600(state, [0x0000000000000001n, 0x0000000000008082n, 0x800000000000808An, 0x8000000080008000n, 0x000000000000808Bn, 0x0000000080000001n, 0x8000000080008081n, 0x8000000000008009n, 0x000000000000008An, 0x0000000000000088n, 0x0000000080008009n, 0x000000008000000An, 0x0000000080008081n, 0x8000000000008080n, 0x0000000000000001n, 0x8000000080008008n, 0x8000000000008089n, 0x800000000000008An, 0x8000000080008009n, 0x8000000000000088n, 0x0000000000008009n, 0x000000000000008An, 0x800000008000000An, 0x8000000080008081n, 0x8000000000008080n, 0x0000000000000001n, 0x8000000080008008n]);
  const output = new Uint8Array(32);
  for (let i = 0; i < 4; i++) { const word = state[i]; for (let j = 0; j < 8; j++) output[i * 8 + j] = Number((word >> (BigInt(j) * 8n)) & 0xFFn); }
  return output;
}
