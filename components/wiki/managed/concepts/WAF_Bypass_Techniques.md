---
type: concept
title: WAF Bypass Techniques
updated: 2026-04-20
source_count: 1
tags: [concept, security, web]
---

# [[WAF Bypass Techniques]]

## Summary
> Methods used to circumvent Web Application Firewalls (WAFs) to deliver payloads or perform reconnaissance.

## Detailed Description
WAFs are designed to filter out malicious traffic, but they often rely on regex patterns or blacklists that can be evaded through various encoding or formatting tricks.

One notable technique is **IP Shortening**, where an IP address is represented in a non-standard format to bypass filters that specifically look for standard dotted-quad notation (e.g., `127.0.0.1`).

Examples of shortened IPs:
- `http://1.0.0.1` → `http://1.1`
- `http://127.0.0.1` → `http://127.1`
- `http://192.168.0.1` → `http://192.168.1`

This technique can bypass WAF filters for SSRF, open-redirect, and other vulnerabilities where an IP input is blacklisted.

## Related Entities / Concepts
- [[Network Reconnaissance]] – bypasses are often needed to scan protected hosts.
- [[Prompt Injection]] – a similar concept of bypassing intended constraints in LLMs.

## Evidence / Sources
- [[2026-04-20_the_book_of_secret_knowledge]] – documents IP shortening and lists other tools for WAF fingerprinting and detection like `WhatWaf`.

## ⚠️ Contradictions / Open Questions
- Efficacy of shortening on modern WAFs that perform canonicalization.

## See Also
- [[MOC: Agentic Frameworks]]
