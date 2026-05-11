// ============================================================================
// ARKHE Ω-TEMP — Address Generation & Validation
// ============================================================================

import { keccak256, keccak256Sync } from '../crypto/keccak';

const ADDRESS_LENGTH = 20; // 160 bits (matching Ethereum compatibility)
const CHECKSUM_LENGTH = 4; // First 4 bytes for simple checksum

/**
 * Generate ARKHE address from name or seed.
 * Uses SHA3-256 and takes the first 20 bytes.
 */
export async function generateAddress(name: string): Promise<string> {
  const hash = await keccak256(new TextEncoder().encode(name));
  return '0x' + bytesToHex(hash.slice(0, ADDRESS_LENGTH));
}

/**
 * Synchronous address generation (uses pure JS keccak)
 */
export function generateAddressSync(name: string): string {
  const hash = keccak256Sync(new TextEncoder().encode(name));
  return '0x' + bytesToHex(hash.slice(0, ADDRESS_LENGTH));
}

/**
 * Validate ARKHE address format
 */
export function isValidAddress(address: string): boolean {
  if (!address || !address.startsWith('0x')) return false;
  const hex = address.slice(2);
  if (hex.length !== ADDRESS_LENGTH * 2) return false;
  return /^[0-9a-fA-F]+$/.test(hex);
}

/**
 * Create checksum address (similar to EIP-55)
 */
export function toChecksumAddress(address: string): string {
  if (!isValidAddress(address)) return address;

  const hex = address.slice(2).toLowerCase();
  const hash = keccak256Sync(new TextEncoder().encode(hex));

  let result = '0x';
  for (let i = 0; i < hex.length; i++) {
    const char = hex[i];
    const hashByte = parseInt(hash[i >> 1].toString(16), 16);
    if ((i % 2 === 0 && hashByte >= 8) || (i % 2 === 1 && (hashByte & 0x0F) >= 8)) {
      result += char.toUpperCase();
    } else {
      result += char;
    }
  }

  return result;
}

/**
 * Short address display (first 6 + last 4 chars)
 */
export function shortAddress(address: string): string {
  if (!isValidAddress(address)) return 'Invalid';
  return address.slice(0, 8) + '...' + address.slice(-6);
}

// Utility functions
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

export function hexToBytes(hex: string): Uint8Array {
  const clean = hex.startsWith('0x') ? hex.slice(2) : hex;
  const bytes = new Uint8Array(clean.length / 2);
  for (let i = 0; i < clean.length; i += 2) {
    bytes[i / 2] = parseInt(clean.slice(i, i + 2), 16);
  }
  return bytes;
}

export function addressDistance(a: string, b: string): number {
  const aBytes = hexToBytes(a.slice(2));
  const bBytes = hexToBytes(b.slice(2));
  let distance = 0;
  for (let i = 0; i < aBytes.length; i++) {
    distance += Math.abs(aBytes[i] - bBytes[i]);
  }
  return distance;
}
