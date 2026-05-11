---
type: source
status: processed
original_source: https://github.com/SimoneAvogadro/android-reverse-engineering-skill
---

# Android Reverse Engineering & API Extraction Skill

This repository provides a Claude Code skill for decompiling Android artifacts (APK, XAPK, JAR, AAR) and extracting HTTP API metadata.

## Core Capabilities
- **Decompilation Engine**: Uses `jadx` and `Vineflower`/`Fernflower` for converting DEX to Java.
- **API Extraction**: Identifies Retrofit endpoints, OkHttp calls, and hardcoded URLs.
- **Auth Pattern Recognition**: Traces authentication headers and tokens throughout the app logic.
- **Call Flow Analysis**: Maps the path from UI components (Activities/Fragments) down to network requests.

## Relevance to Arkhe(n)
The Arkhe(n) monorepo includes an `android/` node implementation. This skill can be utilized to audit the Arkhe Android node for leaked API keys, unauthorized network endpoints, or deviations from the EQBE ethical protocol in its network communications.
