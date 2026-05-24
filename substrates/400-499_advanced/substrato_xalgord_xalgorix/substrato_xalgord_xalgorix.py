import json
import tempfile
import os
import hashlib

class SubstratoXalgorix:
    def canonize(self):
        report = {
            "Title": "Xalgorix - The Most Powerful Open-Source AI Pentesting Agent",
            "Description": "Xalgorix is a self-hosted AI security testing platform for authorized penetration testing and bug bounty workflows. It combines an LLM-driven agent, browser automation, terminal tooling, a 22-phase testing methodology, live WebSocket events, finding management, report generation, and integrations for AgentMail and Discord.",
            "Features": [
                "Dashboard: Local Web UI on 127.0.0.1:9137 by default, scan management, live status, bulk scan actions, and historical scan recovery.",
                "Scanning: Single target, DAST, wildcard, and multi-target flows with selectable methodology phases.",
                "Live telemetry: Tool calls, agent messages, findings, errors, HTTP activity, and LLM activity over WebSockets.",
                "Findings: Scan detail pages, severity filters, CVSS details, finding index, and verified finding workflows.",
                "Reporting: Branded PDF reports with target/company name, uploaded logo, report list, open/download/delete actions.",
                "Integrations: AgentMail test inboxes, verification emails, OTP flows, email triage events, and Discord notifications.",
                "Configuration: Dashboard settings for LLM, AgentMail, Discord, proxy, runtime, browser, auth, rate limits, and resources.",
                "Runtime safety: Resource-aware instance limits and loopback-only binding unless external access is explicitly configured with auth."
            ],
            "Architecture": [
                "Scan Modes: Single target, Wildcard / multi, DAST",
                "Methodology: 22 phases including Reconnaissance, Authentication testing, Injection, SSRF, IDOR, API testing, Zero-day discovery, etc.",
                "Reports: PDF files including Summary, Findings, Evidence, Remediation, Branding",
                "API: REST API endpoints for scan management, status, instances, settings",
                "Integrations: Discord, Caido, AgentMail"
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_xalgorix_")
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print("Canonized Xalgorix. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoXalgorix()
    substrate.canonize()
