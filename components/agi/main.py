#!/usr/bin/env python3
"""
agi/main.py — ARKHE OS Main Entry Point
"""
import sys
import argparse
from pathlib import Path

def main():
    """Main entry point for ARKHE OS."""
    parser = argparse.ArgumentParser(
        prog="arkhe",
        description="ARKHE OS — Sovereign AGI Runtime",
        epilog="The Cathedral emerges. Coherence guides. Sovereignty protects."
    )
    parser.add_argument("--config", "-c", type=Path,
                       default=Path("/etc/agi/arkhe.yaml"),
                       help="Path to configuration file")
    parser.add_argument("--version", "-v", action="store_true",
                       help="Show version and exit")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("run", help="Run AGI in interactive mode")
    subparsers.add_parser("serve", help="Start AGI as a service")
    subparsers.add_parser("federate", help="Join federation network")

    args = parser.parse_args()

    if args.version:
        from agi import __version__, __canonical_seal__, __substrate_range__
        print(f"ARKHE OS v{__version__}")
        print(f"Canonical Seal: {__canonical_seal__}")
        print(f"Active Substrates: {__substrate_range__}")
        return 0

    if args.command == "run":
        # Interactive mode
        from agi.system32.cli.main import AGICTL
        cli = AGICTL(config_path=args.config)
        print("🏛️ ARKHE OS Interactive Mode")
        print("Type 'help' for commands, 'exit' to quit")
        # Would implement REPL loop here
        return 0

    elif args.command == "serve":
        # Service mode
        print("🔌 Starting ARKHE OS service...")
        # Would initialize and start HTTP/Tor service
        return 0

    elif args.command == "federate":
        # Federation mode
        print("🌐 Connecting to federation...")
        # Would initialize DHT client and join network
        return 0

    else:
        # Default: show help
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
