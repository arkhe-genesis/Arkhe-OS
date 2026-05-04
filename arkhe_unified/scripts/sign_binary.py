#!/usr/bin/env python3
"""
scripts/sign_binary.py — Assinatura digital de binários ARKHE OS
Usa Ed25519 para assinatura rápida e verificável.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    print("❌ Required: pip install PyNaCl")
    sys.exit(1)


def compute_sha256(filepath: Path) -> str:
    """Computar hash SHA-256 de arquivo."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def sign_binary(
    binary_path: Path,
    private_key: Optional[bytes] = None,
    key_file: Optional[Path] = None,
    output_sig: Optional[Path] = None
) -> tuple[bytes, str]:
    """
    Assinar binário com chave Ed25519.

    Returns:
        (signature_bytes, binary_hash)
    """
    # Carregar chave privada
    if private_key:
        signing_key = SigningKey(private_key)
    elif key_file:
        with open(key_file, 'rb') as f:
            key_data = f.read().strip()
            if len(key_data) == 64:  # Seed hex
                signing_key = SigningKey(bytes.fromhex(key_data.decode()))
            elif len(key_data) == 32:  # Raw seed
                signing_key = SigningKey(key_data)
            else:
                raise ValueError(f"Invalid key format in {key_file}")
    else:
        # Gerar nova chave para demonstração (NÃO usar em produção!)
        print("⚠️  No key provided — generating ephemeral key (NOT FOR PRODUCTION)")
        signing_key = SigningKey.generate()
        print(f"🔑 Generated key (hex): {signing_key.encode().hex()}")
        print("💾 Save this key securely for future verification!")

    # Computar hash do binário
    binary_hash = compute_sha256(binary_path)
    print(f"🔐 Binary hash: {binary_hash}")

    # Assinar hash (não o binário inteiro para eficiência)
    signature = signing_key.sign(binary_hash.encode()).signature

    # Salvar assinatura se especificado
    if output_sig:
        with open(output_sig, 'wb') as f:
            f.write(signature)
        print(f"✅ Signature saved to {output_sig}")

    return signature, binary_hash


def verify_signature(
    binary_path: Path,
    signature_path: Path,
    public_key: Optional[bytes] = None,
    key_file: Optional[Path] = None
) -> bool:
    """Verificar assinatura de binário."""
    # Carregar chave pública
    if public_key:
        verify_key = VerifyKey(public_key)
    elif key_file:
        with open(key_file, 'rb') as f:
            key_data = f.read().strip()
            if len(key_data) == 64:  # Public key hex
                verify_key = VerifyKey(bytes.fromhex(key_data.decode()))
            elif len(key_data) == 32:  # Raw public key
                verify_key = VerifyKey(key_data)
            else:
                raise ValueError(f"Invalid public key format in {key_file}")
    else:
        raise ValueError("Must provide public key via --public-key or --public-key-file")

    # Computar hash do binário
    binary_hash = compute_sha256(binary_path)

    # Ler assinatura
    with open(signature_path, 'rb') as f:
        signature = f.read()

    if len(signature) != 64:
        print(f"❌ Invalid signature length: {len(signature)} (expected 64)")
        return False

    # Verificar
    try:
        verify_key.verify(binary_hash.encode(), signature)
        print("✅ Signature verified successfully")
        return True
    except BadSignatureError:
        print("❌ Signature verification FAILED")
        return False


def generate_keypair(output_dir: Path) -> tuple[Path, Path]:
    """Gerar par de chaves Ed25519 e salvar em arquivos."""
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    private_path = output_dir / "arkhe_private.key"
    public_path = output_dir / "arkhe_public.key"

    with open(private_path, 'wb') as f:
        f.write(signing_key.encode())

    with open(public_path, 'wb') as f:
        f.write(verify_key.encode())

    print(f"🔑 Private key: {private_path} (KEEP SECRET)")
    print(f"🔓 Public key: {public_path} (distribute freely)")
    print(f"📋 Public key (hex): {verify_key.encode().hex()}")

    return private_path, public_path


def main():
    parser = argparse.ArgumentParser(description="ARKHE OS Binary Signing Tool")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subcommand: sign
    sign_parser = subparsers.add_parser('sign', help='Sign a binary')
    sign_parser.add_argument('binary', type=Path, help='Path to binary to sign')
    sign_parser.add_argument('-k', '--key-file', type=Path, help='Path to private key file')
    sign_parser.add_argument('-o', '--output', type=Path, help='Output path for signature (.sig)')
    sign_parser.add_argument('--key-hex', type=str, help='Private key as hex string (use with caution)')

    # Subcommand: verify
    verify_parser = subparsers.add_parser('verify', help='Verify a binary signature')
    verify_parser.add_argument('binary', type=Path, help='Path to binary to verify')
    verify_parser.add_argument('-s', '--signature', type=Path, required=True, help='Path to signature file')
    verify_parser.add_argument('-p', '--public-key', type=Path, help='Path to public key file')
    verify_parser.add_argument('--public-key-hex', type=str, help='Public key as hex string')

    # Subcommand: keygen
    keygen_parser = subparsers.add_parser('keygen', help='Generate new keypair')
    keygen_parser.add_argument('-o', '--output-dir', type=Path, default='.', help='Output directory for keys')

    args = parser.parse_args()

    if args.command == 'sign':
        private_key = None
        if args.key_hex:
            private_key = bytes.fromhex(args.key_hex)

        sig_path = args.output or args.binary.with_suffix('.sig')
        sign_binary(args.binary, private_key, args.key_file, sig_path)

    elif args.command == 'verify':
        public_key = None
        if args.public_key_hex:
            public_key = bytes.fromhex(args.public_key_hex)

        success = verify_signature(args.binary, args.signature, public_key, args.public_key)
        sys.exit(0 if success else 1)

    elif args.command == 'keygen':
        args.output_dir.mkdir(parents=True, exist_ok=True)
        generate_keypair(args.output_dir)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
