---
type: concept
title: Sensitive Information Disclosure
updated: 2026-04-06
source_count: 1
tags: [concept, security, privacy]
---

# [[Sensitive Information Disclosure]]

## Summary
> Unintentional leakage of confidential data, including PII, trade secrets, or internal system prompts.

## Detailed Description
Occurs when an LLM reveals information it was not supposed to share. This can happen through "memorization" of training data or by failing to redact sensitive information in its output.

## Related Entities / Concepts
- [[Prompt Injection]] – common method to trigger disclosure.
- [[System Prompt Leakage]] – sub-category of disclosure.

## Evidence / Sources
- [[2026-04-06_ai_pentest_toolkit]] – identifies LLM02 and LLM07.

## ⚠️ Contradictions / Open Questions
- Is "forgetting" sensitive data from a trained model possible without full retraining?

## See Also
- [[MOC: Data Privacy in AI]]
