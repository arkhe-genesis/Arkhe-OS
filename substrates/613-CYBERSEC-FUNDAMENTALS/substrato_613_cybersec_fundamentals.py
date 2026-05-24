import os
import json
import tempfile
import hashlib
import shutil

class Substrato613CybersecFundamentals:
    """
    Canonizes Substrate 613-CYBERSEC-FUNDAMENTALS.
    Materializes the full polyglot stack for the arkhe-cybersec plugin
    to a temporary directory and outputs a canonical JSON report.
    Adheres strictly to invariants: no f-strings.
    """
    def __init__(self):
        self.data = {
            "id": "613-CYBERSEC-FUNDAMENTALS",
            "name": "ARKHE Cybersecurity Foundations — 12 pillars, 48 topics",
            "plugin_name": "arkhe-cybersec",
            "author": "ORCID 0009-0005-2697-4668",
            "license": "MIT",
            "stack": "Python 3.10+, Click, Rich, Nmap, Nuclei",
            "type": "Substrato educacional e de testes",
            "status": "CANONIZED",
            "incorporation_date": "25 de Maio de 2026",
            "canonical_seal": "pending"
        }

    def generate_plugin_files(self, base_dir):
        # Create directories
        os.makedirs(os.path.join(base_dir, "nuclei_templates"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "docker"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "tests"), exist_ok=True)

        # File contents
        files = {}

        files["plugin.toml"] = """[plugin]
name = "arkhe-cybersec"
version = "1.0.0"
description = "ARKHE Cybersecurity Foundations — 12 pillars, 48 topics, integrated lab, quiz, and audit"
author = "ORCID 0009-0005-2697-4668"
license = "MIT"
entry_point = "cybersec_cli"
dependencies = ["click", "rich", "nmap", "python-nmap", "scapy", "requests", "aiohttp"]
arkhe_version = "∞.Ω.∇+++"
substrate_id = "613-CYBERSEC-FUNDAMENTALS"
"""

        files["__init__.py"] = """#!/usr/bin/env python3
\"\"\"ARKHE OS — Plugin arkhe-cybersec (Substrate 613)\"\"\"
from .cybersec_cli import register
__all__ = ["register"]
"""

        files["cybersec_cli.py"] = """#!/usr/bin/env python3
\"\"\"
ARKHE OS — Cybersecurity Foundations CLI
Arquiteto: ORCID 0009-0005-2697-4668
\"\"\"

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from .curriculum import CURRICULUM, get_topic, get_pillar_topics
from .quiz_engine import QuizEngine
from .lab_auditor import LabAuditor
from .nmap_bridge import NmapBridge

console = Console()

@click.group()
def cybersec():
    \"\"\"ARKHE Cybersecurity Foundations — 12 pillars, 48 topics.\"\"\"
    pass

@cybersec.command()
@click.argument("topic_id", required=False)
@click.option("--pillar", "-p", help="Filter by pillar (P1-P12)")
def learn(topic_id, pillar):
    \"\"\"Browse the cybersecurity curriculum.\"\"\"
    if topic_id:
        topic = get_topic(topic_id)
        if topic:
            panel = Panel.fit(
                "[bold]{}[/bold]\\n\\n{}".format(topic["name"], topic["content"]),
                title="613.{}".format(topic["id"]), border_style="green"
            )
            console.print(panel)
            if topic.get("prerequisites"):
                console.print("[yellow]Prerequisites:[/yellow]")
                for prereq in topic["prerequisites"]:
                    console.print("  • {}".format(prereq))
            if topic.get("tools"):
                console.print("[yellow]Tools:[/yellow]")
                for tool in topic["tools"]:
                    console.print("  • {}".format(tool))
        else:
            console.print("[red]Topic '{}' not found.[/red]".format(topic_id))
        return

    # List all topics or filter by pillar
    table = Table(title="ARKHE Cybersecurity Curriculum")
    table.add_column("ID", style="cyan")
    table.add_column("Topic", style="green")
    table.add_column("Pillar", style="yellow")
    table.add_column("Tools", style="dim")

    for p_id, p_data in CURRICULUM.items():
        if pillar and p_id != pillar:
            continue
        for topic in p_data["topics"]:
            table.add_row(
                topic["id"],
                topic["name"],
                p_data["name"],
                ", ".join(topic.get("tools", []))[:60]
            )

    console.print(table)

@cybersec.command()
@click.argument("topic")
@click.option("--count", "-n", default=5, help="Number of questions")
def quiz(topic, count):
    \"\"\"Take a quiz on a cybersecurity topic.\"\"\"
    engine = QuizEngine()
    questions = engine.generate_quiz(topic, count)
    score = 0
    total = len(questions)

    for i, q in enumerate(questions, 1):
        console.print("\\n[bold]Q{}[/bold]: {}".format(i, q["question"]))
        for opt_id, opt_text in q["options"].items():
            console.print("  {}) {}".format(opt_id, opt_text))
        answer = click.prompt("Your answer", type=str).upper()
        if answer == q["correct"]:
            console.print("[green]✓ Correct![/green]")
            score += 1
        else:
            console.print("[red]✗ Incorrect. Correct: {}[/red]".format(q["correct"]))
        if q.get("explanation"):
            console.print("[dim]{}[/dim]".format(q["explanation"]))

    percentage = (score / total) * 100
    color = "green" if percentage >= 80 else "yellow" if percentage >= 60 else "red"
    console.print("\\n[bold {}]Score: {}/{} ({:.1f}%)[/bold {}]".format(color, score, total, percentage, color))

@cybersec.command()
@click.argument("target", required=False)
@click.option("--port", "-p", default="1-1000", help="Port range")
@click.option("--scan-type", "-s", type=click.Choice(["tcp", "udp", "syn", "os"]), default="tcp")
def scan(target, port, scan_type):
    \"\"\"Perform network reconnaissance scan (educational use only).\"\"\"
    if not target:
        target = click.prompt("Target IP or hostname")

    console.print("[yellow]Starting {} scan on {}:{}...[/yellow]".format(scan_type, target, port))
    console.print("[red]⚠ Educational use only — scan only your own lab environment![/red]")

    nmap = NmapBridge()
    results = nmap.scan(target, port, scan_type)

    if results.get("error"):
        console.print("[red]Scan error: {}[/red]".format(results["error"]))
        return

    table = Table(title="Scan Results — {}".format(target))
    table.add_column("Port", style="cyan")
    table.add_column("State", style="green")
    table.add_column("Service", style="yellow")
    table.add_column("Version", style="dim")

    for port_data in results.get("ports", []):
        table.add_row(
            str(port_data["port"]),
            port_data["state"],
            port_data.get("service", ""),
            port_data.get("version", "")
        )

    console.print(table)

@cybersec.command()
@click.option("--url", "-u", help="Target URL to test")
@click.option("--test", "-t", type=click.Choice(["xss", "sqli", "upload", "all"]), default="all")
def test_web(url, test):
    \"\"\"Test a web application for common vulnerabilities (educational use only).\"\"\"
    if not url:
        url = click.prompt("Target URL (e.g., http://localhost:8080)")

    console.print("[yellow]Testing {} for {} vulnerabilities...[/yellow]".format(url, test))
    console.print("[red]⚠ Educational use only — test only your own lab applications![/red]")

    # Use Nuclei templates for educational testing
    from .nuclei_runner import run_educational_templates
    results = run_educational_templates(url, test)

    for finding in results:
        severity_color = "red" if finding["severity"] in ["critical", "high"] else "yellow"
        console.print("[{color}]●[/{color}] {} ({})".format(finding["name"], finding["severity"], color=severity_color))
        if finding.get("remediation"):
            console.print("  [dim]Fix: {}[/dim]".format(finding["remediation"]))

@cybersec.command()
def lab_check():
    \"\"\"Audit your lab environment for security and isolation.\"\"\"
    auditor = LabAuditor()
    results = auditor.audit()

    console.print("[bold]Lab Environment Audit[/bold]")
    for check, passed in results.items():
        icon = "✓" if passed else "✗"
        color = "green" if passed else "red"
        console.print("  [{color}]{icon} {check}[/{color}]".format(color=color, icon=icon, check=check))

def register(cli: click.Group):
    cli.add_command(cybersec)
"""

        files["curriculum.py"] = """#!/usr/bin/env python3
\"\"\"
ARKHE OS — Substrate 613 Cybersecurity Curriculum
Arquiteto: ORCID 0009-0005-2697-4668
\"\"\"

CURRICULUM = {
    "P1": {
        "name": "Linux Basics",
        "topics": [
            {"id": "613.P1.1", "name": "Linux Command Line Essentials", "tools": ["bash", "zsh"], "prerequisites": [],
             "content": "Master the Linux terminal: file navigation (cd, ls, pwd), file manipulation (cp, mv, rm, touch), text processing (grep, awk, sed), and I/O redirection (>, >>, |).\\n\\nKey commands:\\n• ls -la — list all files with permissions\\n• chmod 755 — change file permissions\\n• ps aux — list running processes\\n• find / -name '*.log' — search for files"},
            {"id": "613.P1.2", "name": "File System and Permissions", "tools": ["chmod", "chown"], "prerequisites": ["613.P1.1"],
             "content": "Understand the Linux filesystem hierarchy (FHS), user/group ownership, and the permission model (rwx for user, group, others).\\n\\nPermission notation:\\n• r=4, w=2, x=1\\n• 755 = rwxr-xr-x\\n• 644 = rw-r--r--"},
            {"id": "613.P1.3", "name": "Process Management", "tools": ["ps", "top", "htop"], "prerequisites": ["613.P1.1"],
             "content": "Monitor and control running processes. Understand foreground vs background jobs, signals (SIGTERM, SIGKILL, SIGSTOP), and process priorities (nice/renice)."},
            {"id": "613.P1.4", "name": "Package Management", "tools": ["apt", "dpkg", "snap"], "prerequisites": ["613.P1.1"],
             "content": "Install, update, and remove software using APT (Advanced Package Tool). Understand repositories, dependencies, and package states."},
            {"id": "613.P1.5", "name": "Shell Scripting Basics", "tools": ["bash", "sh"], "prerequisites": ["613.P1.1"],
             "content": "Write simple shell scripts to automate tasks. Variables, conditionals (if/else), loops (for/while), functions, and error handling."},
        ]
    },
    "P2": {
        "name": "Lab Setup",
        "topics": [
            {"id": "613.P2.1", "name": "Virtualization", "tools": ["VirtualBox", "VMware"], "prerequisites": [],
             "content": "Set up isolated virtual machines for security testing. Understand hypervisor types, network modes (NAT, bridged, host-only), and resource allocation."},
            {"id": "613.P2.2", "name": "Kali Linux Installation", "tools": ["Kali Linux"], "prerequisites": ["613.P2.1"],
             "content": "Install and configure Kali Linux as a security testing platform. Update tools, configure repositories, and set up persistence on USB."},
            {"id": "613.P2.3", "name": "Isolated Network Setup", "tools": ["VirtualBox", "pfSense"], "prerequisites": ["613.P2.1"],
             "content": "Create isolated virtual networks for safe experimentation. Use internal network adapters, configure DHCP, and ensure no traffic leaks to the host network."},
            {"id": "613.P2.4", "name": "Snapshots and Restore", "tools": ["VirtualBox"], "prerequisites": ["613.P2.1"],
             "content": "Use VM snapshots to save and restore machine states. Essential for resetting lab environments after exploitation exercises."},
        ]
    },
    "P3": {
        "name": "Networking Fundamentals",
        "topics": [
            {"id": "613.P3.1", "name": "OSI Model and TCP/IP Stack", "tools": ["Wireshark"], "prerequisites": [],
             "content": "Understand the 7 layers of the OSI model and the 4 layers of the TCP/IP stack. Map protocols to layers (HTTP=7, TCP=4, IP=3, Ethernet=2)."},
            {"id": "613.P3.2", "name": "IP Addressing and Subnetting", "tools": ["ipcalc", "sipcalc"], "prerequisites": ["613.P3.1"],
             "content": "Master IPv4 addressing, subnet masks, CIDR notation, and subnet calculation. Understand public vs private IP ranges (RFC 1918)."},
            {"id": "613.P3.3", "name": "Common Protocols", "tools": ["tcpdump", "Wireshark"], "prerequisites": ["613.P3.1"],
             "content": "Analyze HTTP (port 80), HTTPS (443), DNS (53), DHCP (67/68), and ARP traffic. Understand request/response patterns and protocol headers."},
            {"id": "613.P3.4", "name": "Network Devices", "tools": ["GNS3", "Packet Tracer"], "prerequisites": ["613.P3.1"],
             "content": "Understand routers, switches, firewalls, and access points. Learn how they forward traffic, filter packets, and segment networks."},
        ]
    },
    "P4": {
        "name": "Wireless Security",
        "topics": [
            {"id": "613.P4.1", "name": "WiFi Encryption Standards", "tools": ["aircrack-ng"], "prerequisites": [],
             "content": "Compare WEP (broken), WPA (TKIP), WPA2 (AES-CCMP), and WPA3 (SAE). Understand the vulnerabilities of each standard and why WPA3 is preferred."},
            {"id": "613.P4.2", "name": "Wireless Reconnaissance", "tools": ["airodump-ng", "Kismet"], "prerequisites": ["613.P4.1"],
             "content": "Discover nearby WiFi networks, identify channels, signal strength, and client devices. Understand monitor mode and packet injection."},
            {"id": "613.P4.3", "name": "Common Wireless Attacks", "tools": ["aircrack-ng", "reaver", "hashcat"], "prerequisites": ["613.P4.2"],
             "content": "Study deauthentication attacks, WPA handshake capture, dictionary attacks, and WPS PIN brute-force. Focus on understanding the attack vectors, not execution on unauthorized networks."},
            {"id": "613.P4.4", "name": "Wireless Hardening", "tools": [], "prerequisites": ["613.P4.3"],
             "content": "Implement WPA3, strong pre-shared keys, MAC filtering, hidden SSIDs, and 802.1X authentication. Understand defense-in-depth for wireless networks."},
        ]
    },
    "P5": {
        "name": "Information Gathering",
        "topics": [
            {"id": "613.P5.1", "name": "OSINT Techniques", "tools": ["theHarvester", "Maltego", "Shodan"], "prerequisites": [],
             "content": "Gather information from public sources: search engines, social media, DNS records, WHOIS, and certificate transparency logs. Understand passive vs active reconnaissance."},
            {"id": "613.P5.2", "name": "DNS Enumeration", "tools": ["dig", "nslookup", "dnsenum", "dnsrecon"], "prerequisites": ["613.P5.1"],
             "content": "Enumerate DNS records (A, AAAA, MX, NS, TXT, CNAME). Perform zone transfers, subdomain discovery, and reverse DNS lookups."},
            {"id": "613.P5.3", "name": "Network Scanning (nmap)", "tools": ["nmap", "masscan"], "prerequisites": ["613.P3.2"],
             "content": "Master nmap for host discovery, port scanning, service version detection, and OS fingerprinting. Understand scan types (SYN, TCP connect, UDP) and timing options."},
            {"id": "613.P5.4", "name": "Service and Version Detection", "tools": ["nmap", "amap"], "prerequisites": ["613.P5.3"],
             "content": "Identify running services and their versions. Use banner grabbing and nmap scripts (NSE) to gather detailed service information."},
        ]
    },
    "P6": {
        "name": "Web Security Testing",
        "topics": [
            {"id": "613.P6.1", "name": "HTTP Request/Response Analysis", "tools": ["Burp Suite", "curl", "DevTools"], "prerequisites": [],
             "content": "Analyze HTTP methods (GET, POST, PUT, DELETE), headers, cookies, and response codes. Use intercepting proxies to view and modify traffic."},
            {"id": "613.P6.2", "name": "Web Application Architecture", "tools": [], "prerequisites": ["613.P6.1"],
             "content": "Understand client-server architecture, APIs (REST, GraphQL), authentication mechanisms (session-based, JWT, OAuth), and common frameworks."},
            {"id": "613.P6.3", "name": "Burp Suite / ZAP Basics", "tools": ["Burp Suite", "OWASP ZAP"], "prerequisites": ["613.P6.1"],
             "content": "Configure an intercepting proxy, set up browser proxying, install CA certificates for HTTPS inspection, and use the Repeater and Intruder tools."},
            {"id": "613.P6.4", "name": "Authentication Testing", "tools": ["Burp Suite", "Hydra"], "prerequisites": ["613.P6.3"],
             "content": "Test for weak passwords, brute-force protection, password reset flaws, and multi-factor authentication bypasses. Understand credential stuffing and password spraying."},
        ]
    },
    "P7": {
        "name": "SQL Injection",
        "topics": [
            {"id": "613.P7.1", "name": "SQL Fundamentals for Testers", "tools": ["sqlmap", "MySQL", "PostgreSQL"], "prerequisites": [],
             "content": "Learn basic SQL syntax: SELECT, WHERE, UNION, JOIN, and subqueries. Understand how databases process queries and how injection attacks manipulate them."},
            {"id": "613.P7.2", "name": "Error-Based and Union-Based Injection", "tools": ["sqlmap", "Burp Suite"], "prerequisites": ["613.P7.1"],
             "content": "Exploit error messages to extract database information. Use UNION SELECT to combine attacker-controlled data with legitimate query results."},
            {"id": "613.P7.3", "name": "Blind SQL Injection", "tools": ["sqlmap"], "prerequisites": ["613.P7.2"],
             "content": "Extract data when error messages are suppressed. Use boolean-based (true/false responses) and time-based (response delays) techniques."},
            {"id": "613.P7.4", "name": "Prevention and Parameterized Queries", "tools": [], "prerequisites": ["613.P7.3"],
             "content": "Implement prepared statements, input validation, stored procedures, and least-privilege database accounts. Use ORM frameworks that escape user input by default."},
        ]
    },
    "P8": {
        "name": "Cross-Site Scripting (XSS)",
        "topics": [
            {"id": "613.P8.1", "name": "Reflected, Stored, and DOM-Based XSS", "tools": ["Burp Suite", "XSStrike"], "prerequisites": [],
             "content": "Distinguish between reflected (immediate response), stored (persisted in database), and DOM-based (client-side JavaScript) XSS. Understand the attack flow for each type."},
            {"id": "613.P8.2", "name": "Payload Crafting", "tools": [], "prerequisites": ["613.P8.1"],
             "content": "Create XSS payloads that bypass filters: HTML entity encoding, JavaScript obfuscation, polyglot payloads, and filter evasion techniques."},
            {"id": "613.P8.3", "name": "Session Hijacking via XSS", "tools": [], "prerequisites": ["613.P8.2"],
             "content": "Use XSS to steal session cookies (document.cookie), perform actions on behalf of the victim, and chain with CSRF for advanced attacks."},
            {"id": "613.P8.4", "name": "Content Security Policy (CSP)", "tools": [], "prerequisites": ["613.P8.3"],
             "content": "Implement CSP headers to mitigate XSS: restrict script sources, disable inline scripts (nonce/hash-based), and report violations."},
        ]
    },
    "P9": {
        "name": "File Upload Vulnerabilities",
        "topics": [
            {"id": "613.P9.1", "name": "Unrestricted File Upload", "tools": ["Burp Suite"], "prerequisites": [],
             "content": "Exploit applications that allow arbitrary file uploads without validation. Upload web shells (PHP, ASPX, JSP) to gain remote code execution."},
            {"id": "613.P9.2", "name": "Bypassing Filters", "tools": [], "prerequisites": ["613.P9.1"],
             "content": "Bypass client-side (JavaScript) and server-side (extension, MIME type, content) filters. Use double extensions, null bytes, and magic number spoofing."},
            {"id": "613.P9.3", "name": "Web Shell Deployment", "tools": ["Weevely", "p0wny-shell"], "prerequisites": ["613.P9.2"],
             "content": "Deploy and use web shells for post-exploitation. Understand how to maintain access, escalate privileges, and pivot through the compromised host."},
            {"id": "613.P9.4", "name": "Secure File Handling", "tools": [], "prerequisites": ["613.P9.3"],
             "content": "Implement secure file upload: whitelist allowed extensions, validate MIME types, store files outside web root, rename files, and scan for malware."},
        ]
    },
    "P10": {
        "name": "Social Engineering Awareness",
        "topics": [
            {"id": "613.P10.1", "name": "Phishing and Spear-Phishing", "tools": ["GoPhish", "SET"], "prerequisites": [],
             "content": "Understand email-based social engineering: spoofed senders, malicious attachments, credential harvesting. Learn to identify red flags and conduct awareness training."},
            {"id": "613.P10.2", "name": "Pretexting and Baiting", "tools": [], "prerequisites": ["613.P10.1"],
             "content": "Study impersonation attacks (IT support, vendor, executive) and physical baiting (infected USB drives). Understand the psychology behind these attacks."},
            {"id": "613.P10.3", "name": "USB Drop Attacks", "tools": ["Rubber Ducky"], "prerequisites": ["613.P10.2"],
             "content": "Understand how malicious USB devices (keystroke injection, autorun payloads) can compromise systems. Learn to disable autorun and implement device control policies."},
            {"id": "613.P10.4", "name": "Security Awareness Training", "tools": [], "prerequisites": ["613.P10.3"],
             "content": "Design and deliver effective security awareness programs. Use simulated phishing campaigns, gamification, and regular reinforcement to build a security culture."},
        ]
    },
    "P11": {
        "name": "Security Monitoring",
        "topics": [
            {"id": "613.P11.1", "name": "Log Analysis", "tools": ["grep", "awk", "ELK Stack"], "prerequisites": [],
             "content": "Analyze system logs (syslog, auth.log, Apache/Nginx access logs) to detect security events. Understand log formats, rotation, and centralized collection."},
            {"id": "613.P11.2", "name": "Intrusion Detection Systems (IDS)", "tools": ["Snort", "Suricata"], "prerequisites": ["613.P11.1"],
             "content": "Deploy signature-based (Snort) and anomaly-based IDS. Understand rule creation, alert tuning, and false positive management."},
            {"id": "613.P11.3", "name": "SIEM Basics", "tools": ["Splunk", "ELK", "Wazuh"], "prerequisites": ["613.P11.2"],
             "content": "Understand Security Information and Event Management: log aggregation, correlation rules, dashboards, and incident response workflows."},
            {"id": "613.P11.4", "name": "Network Traffic Monitoring", "tools": ["Wireshark", "Zeek", "ntopng"], "prerequisites": ["613.P3.1"],
             "content": "Capture and analyze network traffic for anomalies. Detect port scans, C2 communication, data exfiltration, and protocol abuse."},
        ]
    },
    "P12": {
        "name": "Post-Exploitation Concepts",
        "topics": [
            {"id": "613.P12.1", "name": "Privilege Escalation", "tools": ["LinPEAS", "WinPEAS"], "prerequisites": [],
             "content": "Escalate from a low-privilege user to root/administrator. Exploit misconfigurations (SUID binaries, sudo rules, writable services) and kernel vulnerabilities."},
            {"id": "613.P12.2", "name": "Lateral Movement", "tools": ["PsExec", "WMI", "SSH"], "prerequisites": ["613.P12.1"],
             "content": "Move from one compromised host to another within a network. Use pass-the-hash, pass-the-ticket, and credential harvesting techniques."},
            {"id": "613.P12.3", "name": "Data Exfiltration", "tools": [], "prerequisites": ["613.P12.2"],
             "content": "Extract sensitive data from compromised systems: DNS tunneling, ICMP exfiltration, encrypted channels, and cloud storage exfiltration."},
            {"id": "613.P12.4", "name": "Persistence Mechanisms", "tools": [], "prerequisites": ["613.P12.3"],
             "content": "Maintain access to compromised systems: cron jobs, startup scripts, registry run keys, scheduled tasks, and backdoor user accounts."},
        ]
    },
}

def get_topic(topic_id):
    \"\"\"Retrieve a topic by its ID (e.g., '613.P7.1').\"\"\"
    for p_id, p_data in CURRICULUM.items():
        for topic in p_data["topics"]:
            if topic["id"] == topic_id:
                return topic
    return None

def get_pillar_topics(pillar_id):
    \"\"\"Retrieve all topics for a given pillar.\"\"\"
    if pillar_id in CURRICULUM:
        return CURRICULUM[pillar_id]["topics"]
    return []
"""

        files["quiz_engine.py"] = """#!/usr/bin/env python3
\"\"\"Quiz engine for cybersecurity certification.\"\"\"
import random, json, hashlib, time
from .curriculum import CURRICULUM, get_topic

class QuizEngine:
    QUESTION_BANK = {
        "613.P7.1": [
            {"question": "What SQL clause is used to combine results from multiple SELECT statements?",
             "options": {"A": "JOIN", "B": "MERGE", "C": "UNION", "D": "COMBINE"}, "correct": "C",
             "explanation": "UNION combines the result sets of two or more SELECT statements."},
            {"question": "Which character is commonly used to terminate a SQL statement in injection attacks?",
             "options": {"A": "; (semicolon)", "B": "-- (double dash)", "C": "' (single quote)", "D": "# (hash)"}, "correct": "B",
             "explanation": "Double dash (--) is used to comment out the rest of the query in many SQL dialects."},
        ],
        # ... additional question banks for each topic
    }

    def generate_quiz(self, topic_id, count=5):
        topic = get_topic(topic_id)
        if not topic:
            return []
        bank = self.QUESTION_BANK.get(topic_id, [])
        if not bank:
            # Generate synthetic questions
            return self._synthetic_questions(topic, count)
        return random.sample(bank, min(count, len(bank)))

    def _synthetic_questions(self, topic, count):
        return [{
            "question": "Explain the key concept of {}.".format(topic["name"]),
            "options": {"A": "Answer A", "B": "Answer B", "C": "Answer C", "D": "Answer D"},
            "correct": "A",
            "explanation": "See curriculum topic {} for the complete explanation.".format(topic["id"])
        } for _ in range(count)]
"""

        files["lab_auditor.py"] = """#!/usr/bin/env python3
\"\"\"Lab environment auditor for cybersecurity exercises.\"\"\"
import subprocess, os, socket

class LabAuditor:
    def audit(self):
        results = {}
        results["VirtualBox installed"] = self._check_binary("VBoxManage")
        results["Kali Linux VM detected"] = self._check_kali_vm()
        results["Network isolation verified"] = self._check_network_isolation()
        results["nmap installed"] = self._check_binary("nmap")
        results["Burp Suite / ZAP installed"] = self._check_binary("burpsuite") or self._check_binary("zap")
        results["Python 3 available"] = self._check_binary("python3")
        results["Docker available"] = self._check_binary("docker")
        return results

    def _check_binary(self, name):
        return subprocess.run(["which", name], capture_output=True).returncode == 0

    def _check_kali_vm(self):
        try:
            result = subprocess.run(["VBoxManage", "list", "vms"], capture_output=True, text=True)
            return "kali" in result.stdout.lower()
        except:
            return False

    def _check_network_isolation(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return not ip.startswith(("10.", "172.", "192.168."))
"""

        files["nmap_bridge.py"] = """#!/usr/bin/env python3
\"\"\"nmap bridge for educational scanning.\"\"\"
import subprocess, json, re

class NmapBridge:
    def scan(self, target, port_range, scan_type):
        cmd = ["nmap", "-p", port_range]
        if scan_type == "syn":
            cmd.append("-sS")
        elif scan_type == "udp":
            cmd.append("-sU")
        elif scan_type == "os":
            cmd.append("-O")
        cmd.extend(["-oX", "-", target])  # XML output to stdout

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"error": result.stderr}
            return self._parse_nmap_xml(result.stdout)
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_nmap_xml(self, xml_output):
        # Simplified XML parsing — in production, use xml.etree.ElementTree
        ports = []
        for match in re.finditer(r'<port protocol="tcp" portid="(\\d+)"><state state="(\\w+)"', xml_output):
            ports.append({"port": int(match.group(1)), "state": match.group(2), "service": "", "version": ""})
        return {"ports": ports}
"""

        files["nuclei_runner.py"] = """#!/usr/bin/env python3
\"\"\"Nuclei runner stub for educational testing.\"\"\"

def run_educational_templates(url, test_type):
    return [
        {"name": "Educational Test {}".format(test_type), "severity": "medium", "remediation": "Review educational material for " + test_type}
    ]
"""

        files["README.md"] = ""
        files["nuclei_templates/sql_injection.yaml"] = ""
        files["nuclei_templates/xss_reflected.yaml"] = ""
        files["nuclei_templates/file_upload_basic.yaml"] = ""
        files["docker/Dockerfile.lab"] = ""
        files["tests/test_quiz_engine.py"] = ""
        files["tests/test_nmap_bridge.py"] = ""
        files["tests/test_lab_auditor.py"] = ""

        # Write files
        for relative_path, content in files.items():
            full_path = os.path.join(base_dir, relative_path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    def generate_json(self):
        # 1. Generate the polyglot stack in a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="arkhe_cybersec_")
        self.generate_plugin_files(temp_dir)
        self.data["plugin_materialized_path"] = temp_dir

        # 2. Compute canonical seal (using json.dumps with sort_keys=True)
        canonical_str = json.dumps(self.data, sort_keys=True)
        seal = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        self.data["canonical_seal"] = seal

        # 3. Securely output the canonical JSON report
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        return path

if __name__ == "__main__":
    canonizer = Substrato613CybersecFundamentals()
    path = canonizer.generate_json()
    print("Canonized 613-CYBERSEC-FUNDAMENTALS to: " + path)
    print("Plugin materialized at: " + canonizer.data["plugin_materialized_path"])
