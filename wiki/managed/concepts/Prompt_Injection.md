---
type: concept
title: Prompt Injection
updated: 2026-04-06
source_count: 1
tags: [concept, security, ai]
---

# [[Prompt Injection]]

## Summary
> Manipulation of LLM input to override original instructions, bypass filters, or extract hidden data.

## Detailed Description
Prompt injection is the AI equivalent of SQL injection. It involves crafting inputs that the model interprets as instructions rather than data. Attacks can be direct (user-to-model) or indirect (model-consumes-malicious-content).

## Related Entities / Concepts
- [[Sensitive Information Disclosure]] – often the goal of injection.
- [[System Prompt Leakage]] – a specific type of injection result.

## Evidence / Sources
- [[2026-04-06_ai_pentest_toolkit]] – defines LLM01 and provides payloads.

## ⚠️ Contradictions / Open Questions
- How to effectively distinguish between "data" and "instruction" in a natural language interface without performance degradation?

## See Also
- [[MOC: LLM Security]]
