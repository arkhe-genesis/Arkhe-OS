#!/usr/bin/env python3
# cathedral_cli.py - Cathedral SecOps Command Line Interface

import argparse
import asyncio
import json
import sys
from utils.cathedral_secops.lab import SovereignLab
from utils.cathedral_secops.crypto import CathedralCryptoKit
from utils.cathedral_secops.cracker import EthicalCracker
from utils.cathedral_secops.wifi import AirGuardian
from utils.cathedral_secops.scanner import NmapSo
from utils.cathedral_secops.sniffer import SovereignShark
from utils.cathedral_secops.phishing import EthicalPhish
from utils.cathedral_secops.monitor import SovereignKeystrokeMonitor
from utils.cathedral_secops.honeypot import SovereignDecoy
from utils.cathedral_secops.forensics import ImmutableInvestigator
from utils.cathedral_secops.headi import SovereignHeadi
from utils.cathedral_secops.gno_auditor import SovereignGnoAuditor
from utils.cathedral_secops.dork_forge import SovereignDorkForge

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║  CATHEDRAL SECOPS — THE INSTRUMENTS OF SOVEREIGN OVERSIGHT            ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def handle_lab(args):
    lab = SovereignLab(args.consent_id)
    result = await lab.create_lab(args.name, args.network, args.tools.split(','))
    print(json.dumps(result, indent=2))

async def handle_crypto(args):
    kit = CathedralCryptoKit(args.consent_id)
    if args.op == "encrypt":
        result = await kit.encrypt(args.data, args.purpose)
    else:
        result = await kit.hash_data(args.data)
    print(json.dumps(result, indent=2))

async def handle_cracker(args):
    cracker = EthicalCracker(args.consent_id)
    result = await cracker.audit(args.target_hashes, args.wordlist, args.consent_token)
    print(json.dumps(result, indent=2))

async def handle_wifi(args):
    ag = AirGuardian(args.consent_id)
    result = await ag.start_passive_scan(args.interface, args.duration)
    print(json.dumps(result, indent=2))

async def handle_scanner(args):
    scanner = NmapSo(args.consent_id)
    result = await scanner.scan(args.target, args.ports, args.consent_token)
    print(json.dumps(result, indent=2))

async def handle_sniffer(args):
    shark = SovereignShark(args.consent_id)
    result = await shark.capture(args.interface, args.duration, args.scope)
    print(json.dumps(result, indent=2))

async def handle_phish(args):
    phish = EthicalPhish(args.consent_id)
    result = await phish.deploy_campaign(args.template, args.targets, args.campaign_id)
    print(json.dumps(result, indent=2))

async def handle_keylogger(args):
    monitor = SovereignKeystrokeMonitor(args.consent_id)
    result = await monitor.start(args.process, args.duration, args.auditors)
    print(json.dumps(result, indent=2))

async def handle_honeypot(args):
    decoy = SovereignDecoy(args.consent_id)
    result = await decoy.deploy(args.agent, args.network, args.scope)
    print(json.dumps(result, indent=2))

async def handle_investigator(args):
    inv = ImmutableInvestigator(args.consent_id)
    result = await inv.analyze(args.evidence, args.case_id, args.query)
    print(json.dumps(result, indent=2))

async def handle_headi(args):
    headi = SovereignHeadi(args.consent_id)
    result = await headi.inject(args.url, args.pfile)
    print(json.dumps(result, indent=2))

async def handle_gno(args):
    auditor = SovereignGnoAuditor(args.consent_id)
    result = await auditor.audit_contract(args.path)
    print(json.dumps(result, indent=2))

async def handle_dork(args):
    forge = SovereignDorkForge(args.consent_id)
    result = await forge.process_dork(args.domain, args.type)
    print(json.dumps(result, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Cathedral SecOps CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common args
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--consent-id", required=True, help="Mandatory Consent ID for SecOps")

    # 1. Lab
    lab_p = subparsers.add_parser("lab", parents=[common_parser])
    lab_p.add_argument("op", choices=["create"])
    lab_p.add_argument("--name", required=True)
    lab_p.add_argument("--network", required=True)
    lab_p.add_argument("--tools", required=True)

    # 2. Crypto
    crypto_p = subparsers.add_parser("crypto", parents=[common_parser])
    crypto_p.add_argument("op", choices=["encrypt", "hash"])
    crypto_p.add_argument("--data", required=True)
    crypto_p.add_argument("--purpose")

    # 3. Cracker
    cracker_p = subparsers.add_parser("cracker", parents=[common_parser])
    cracker_p.add_argument("op", choices=["audit"])
    cracker_p.add_argument("--target-hashes", required=True)
    cracker_p.add_argument("--wordlist", required=True)
    cracker_p.add_argument("--consent-token", required=True)

    # 4. WiFi
    wifi_p = subparsers.add_parser("wifi", parents=[common_parser])
    wifi_p.add_argument("op", choices=["scan"])
    wifi_p.add_argument("--interface", required=True)
    wifi_p.add_argument("--duration", type=int, default=300)

    # 5. Scanner
    scanner_p = subparsers.add_parser("scan", parents=[common_parser])
    scanner_p.add_argument("--target", required=True)
    scanner_p.add_argument("--ports", required=True)
    scanner_p.add_argument("--consent-token", required=True)

    # 6. Sniffer
    sniffer_p = subparsers.add_parser("sniffer", parents=[common_parser])
    sniffer_p.add_argument("--interface", required=True)
    sniffer_p.add_argument("--duration", type=int, default=60)
    sniffer_p.add_argument("--scope", required=True)

    # 7. Phish
    phish_p = subparsers.add_parser("phish", parents=[common_parser])
    phish_p.add_argument("op", choices=["deploy"])
    phish_p.add_argument("--template", required=True)
    phish_p.add_argument("--targets", required=True)
    phish_p.add_argument("--campaign-id", required=True)

    # 8. Keylogger
    keylogger_p = subparsers.add_parser("keylogger", parents=[common_parser])
    keylogger_p.add_argument("op", choices=["start"])
    keylogger_p.add_argument("--process", required=True)
    keylogger_p.add_argument("--duration", type=int, required=True)
    keylogger_p.add_argument("--auditors", required=True)

    # 9. Honeypot
    honeypot_p = subparsers.add_parser("honeypot", parents=[common_parser])
    honeypot_p.add_argument("op", choices=["deploy"])
    honeypot_p.add_argument("--agent", required=True)
    honeypot_p.add_argument("--network", required=True)
    honeypot_p.add_argument("--scope", required=True)

    # 10. Investigator
    investigator_p = subparsers.add_parser("investigator", parents=[common_parser])
    investigator_p.add_argument("op", choices=["analyze"])
    investigator_p.add_argument("--evidence", required=True)
    investigator_p.add_argument("--case-id", required=True)
    investigator_p.add_argument("--query", required=True)

    # 11. Headi
    headi_p = subparsers.add_parser("headi", parents=[common_parser])
    headi_p.add_argument("-u", "--url", required=True, help="Target URL")
    headi_p.add_argument("-p", "--pfile", help="Payload File")

    # 12. GnoAuditor
    gno_p = subparsers.add_parser("gno", parents=[common_parser])
    gno_p.add_argument("op", choices=["audit"])
    gno_p.add_argument("--path", required=True, help="Contract Path")

    # 13. Dork Forge
    dork_p = subparsers.add_parser("dork", parents=[common_parser])
    dork_p.add_argument("--domain", required=True, help="Target Domain")
    dork_p.add_argument("--type", choices=["files", "open_dirs", "login_pages", "exposed_config"], required=True)

    args = parser.parse_args()
    print_banner()

    if args.command == "lab":
        asyncio.run(handle_lab(args))
    elif args.command == "crypto":
        asyncio.run(handle_crypto(args))
    elif args.command == "cracker":
        asyncio.run(handle_cracker(args))
    elif args.command == "wifi":
        asyncio.run(handle_wifi(args))
    elif args.command == "scan":
        asyncio.run(handle_scanner(args))
    elif args.command == "sniffer":
        asyncio.run(handle_sniffer(args))
    elif args.command == "phish":
        asyncio.run(handle_phish(args))
    elif args.command == "keylogger":
        asyncio.run(handle_keylogger(args))
    elif args.command == "honeypot":
        asyncio.run(handle_honeypot(args))
    elif args.command == "investigator":
        asyncio.run(handle_investigator(args))
    elif args.command == "headi":
        asyncio.run(handle_headi(args))
    elif args.command == "gno":
        asyncio.run(handle_gno(args))
    elif args.command == "dork":
        asyncio.run(handle_dork(args))

if __name__ == "__main__":
    main()
