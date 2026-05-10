---
type: concept
title: Network Reconnaissance
updated: 2026-04-20
source_count: 1
tags: [concept, security, networking]
---

# [[Network Reconnaissance]]

## Summary
> The process of gathering information about a target network to identify its structure, assets, and potential vulnerabilities.

## Detailed Description
Network reconnaissance involves using various tools to discover active hosts, open ports, running services, and operating system versions. It is often the first phase of a penetration test or a security audit.

Key techniques include:
- **Port Scanning**: Identifying open ports to determine available services.
- **Service Enumeration**: Gathering details about specific versions of software running on open ports.
- **Network Mapping**: Visualizing the topology and interconnectivity of network devices.

## Related Entities / Concepts
- [[Agentic Pentesting]] – uses reconnaissance data for autonomous decision-making.
- [[WAF Bypass Techniques]] – often employed during reconnaissance to evade detection.

## Evidence / Sources
- [[2026-04-20_the_book_of_secret_knowledge]] – lists numerous tools like `nmap`, `masscan`, `zmap`, and `pbscan` for efficient reconnaissance.

## ⚠️ Contradictions / Open Questions
- Passive vs. Active reconnaissance: The trade-off between information depth and stealth.

## See Also
- [[MOC: Agentic Frameworks]]
