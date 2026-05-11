#!/usr/bin/env python3
"""
arkhe-verify — CLI script for validating ARKHE OS package integrity
"""
import sys
import argparse
from pathlib import Path

# Injeta a raiz do projeto no PYTHONPATH para ser executável sem install
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from arkhe_os.utils.ontological_imports import (
    seal_package_with_arkh,
    verify_arkh_seal,
    export_ontology_manifest,
    get_package_metadata
)

def cmd_seal(args):
    pkg_path = Path(args.package_path)
    secret_key = bytes.fromhex(args.key) if args.key else None

    try:
        result = seal_package_with_arkh(pkg_path, secret_key)
        print(f"✅ Package {pkg_path} successfully sealed.")
        print(f"Magic: {result['magic']}")
        print(f"Hash: {result['content_hash']}")
        print(f"Signature: {result['signature']}")
        print(f"File: {result['integrity_file']}")
        if not args.key:
            print(f"🔑 Generated Secret Key (SAVE THIS!): {result['secret_key']}")
        return 0
    except Exception as e:
        print(f"❌ Failed to seal package: {e}", file=sys.stderr)
        return 1

def cmd_verify(args):
    pkg_path = Path(args.package_path)
    if not args.key:
        print("❌ Error: A secret key (--key) is required to verify the seal.", file=sys.stderr)
        return 1

    try:
        secret_key = bytes.fromhex(args.key)
        is_valid = verify_arkh_seal(pkg_path, secret_key)
        if is_valid:
            print(f"✅ Seal is VALID for package {pkg_path}.")
            return 0
        else:
            print(f"❌ Seal is INVALID or missing for package {pkg_path}.", file=sys.stderr)
            return 1
    except ValueError:
         print("❌ Error: Invalid key format. Must be a hex string.", file=sys.stderr)
         return 1
    except Exception as e:
        print(f"❌ Verification error: {e}", file=sys.stderr)
        return 1

def cmd_manifest(args):
    try:
        out_path = Path(args.output) if args.output else None
        result_path = export_ontology_manifest(out_path)
        print(f"✅ Manifest exported to: {result_path}")
        return 0
    except Exception as e:
        print(f"❌ Failed to export manifest: {e}", file=sys.stderr)
        return 1

def cmd_info(args):
    try:
        metadata = get_package_metadata()
        for k, v in metadata.items():
            print(f"{k.capitalize()}: {v}")
        return 0
    except Exception as e:
        print(f"❌ Error fetching metadata: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(description="ARKHE OS Ontology Integrity CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: seal
    parser_seal = subparsers.add_parser("seal", help="Seal the package with an ARKH signature")
    parser_seal.add_argument("package_path", type=str, help="Path to the package directory (e.g., arkhe_os)")
    parser_seal.add_argument("--key", type=str, help="Hex-encoded secret key (generated automatically if omitted)")

    # Subcommand: verify
    parser_verify = subparsers.add_parser("verify", help="Verify the ARKH seal of a package")
    parser_verify.add_argument("package_path", type=str, help="Path to the package directory")
    parser_verify.add_argument("--key", type=str, required=True, help="Hex-encoded secret key for verification")

    # Subcommand: manifest
    parser_manifest = subparsers.add_parser("manifest", help="Export the ontological manifest of the package")
    parser_manifest.add_argument("--output", type=str, help="Output file path (default: ontology_manifest.json)")

    # Subcommand: info
    parser_info = subparsers.add_parser("info", help="Show package metadata")

    args = parser.parse_args()

    if args.command == "seal":
        sys.exit(cmd_seal(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "manifest":
        sys.exit(cmd_manifest(args))
    elif args.command == "info":
        sys.exit(cmd_info(args))

if __name__ == "__main__":
    main()
